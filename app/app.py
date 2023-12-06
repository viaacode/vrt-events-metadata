#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from io import BytesIO
from hashlib import md5


import requests
from mediahaven import MediaHaven
from mediahaven.resources.base_resource import MediaHavenPageObject
from mediahaven.mediahaven import MediaHavenException
from mediahaven.oauth2 import RequestTokenError, ROPCGrant
from pika.exceptions import AMQPConnectionError
from requests.exceptions import HTTPError, RequestException
from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.helpers.events_parser import EventParser
from app.helpers.xml_helper import (
    transform_to_ebucore,
    construct_sidecar,
    generate_make_subtitle_available_request_xml,
)
from app.services.rabbit import RabbitClient
from app.services.ftp import FTPClient
from app.models.exceptions import InvalidEventException

SLEEP_TIME = 0.7


class NackException(Exception):
    """Exception raised when there is a situation in which handling
    of the event should be stopped.
    """

    def __init__(self, message, requeue=False, **kwargs):
        self.message = message
        self.requeue = requeue
        self.kwargs = kwargs


class EventListener:
    def __init__(self):
        configParser = ConfigParser()
        self.log = logging.get_logger(__name__, config=configParser)
        self.config = configParser.app_cfg
        self.ftp_client = FTPClient(configParser)

        mediahaven_config = self.config["mediahaven"]
        client_id = mediahaven_config["client_id"]
        client_secret = mediahaven_config["client_secret"]
        user = mediahaven_config["username"]
        password = mediahaven_config["password"]
        url = mediahaven_config["host"]
        grant = ROPCGrant(url, client_id, client_secret)
        try:
            grant.request_token(user, password)
        except RequestTokenError as e:
            self.log.error(e)
            raise e

        self.mediahaven_client = MediaHaven(url, grant)
        self.event_parser = EventParser()
        self.queue_name = self.config["rabbitmq"]["queue"]

        try:
            self.rabbit_client = RabbitClient()
        except AMQPConnectionError as error:
            self.log.error("Connection to RabbitMQ failed.")
            raise error

    def _parse_event(self, method, properties, body):
        event_type = method.routing_key.split(".")[-1]

        try:
            event = self.event_parser.get_event(event_type, body)
            self.log.info(f"Got an {event_type} for {event.metadata.media_id}.")
        except InvalidEventException as error:
            raise NackException(
                "Unable to parse the incoming event",
                error=error,
                body=body,
            )

        return event

    def _get_items_for_media_id(self, event):
        try:
            result = self.mediahaven_client.records.search(
                q=f"+(dc_identifier_localid:{event.metadata.media_id})",
            )
            time.sleep(SLEEP_TIME)
        except MediaHavenException as error:
            raise NackException(
                "Failed to search records in MediaHaven.",
                error=error,
                media_id=event.metadata.media_id,
            )
        except RequestException as error:
            raise NackException(
                "Error connecting to MediaHaven, retrying....",
                requeue=True,
                error=error,
            )

        if result.total_nr_of_results == 0:
            raise NackException(
                "Nothing found in MH for media id",
                media_id=event.metadata.media_id,
            )

        return result

    def _get_fragment(self, items: MediaHavenPageObject, event):
        try:
            fragment = next(
                item for item in items.as_generator() if item.Internal.IsFragment
            )

            return fragment
        except StopIteration:
            raise NackException(
                "Fragment not found in MH for media id",
                media_id=event.metadata.media_id,
            )

    def _delete_existing_metadata_collateral(
        self, items: MediaHavenPageObject, fragment
    ):
        try:
            fragment_pid = fragment.Dynamic.PID

            collateral = next(
                item
                for item in items.as_generator()
                if item.Administrative.ExternalId == f"{fragment_pid}_metadata"
            )

            collateral_fragment_id = collateral.Internal.FragmentId

            self.log.info(
                f"Deleting existing metadata collateral for {fragment_pid}.",
                pid=fragment_pid,
                collateral_fragment_id=collateral_fragment_id,
            )

            self.mediahaven_client.records.delete(collateral_fragment_id)
            time.sleep(SLEEP_TIME)
        except StopIteration:
            # No existing collateral, do nothing
            pass
        except MediaHavenException as error:
            raise NackException(
                "Failed to delete collateral in MediaHaven.",
                error=error,
                collateral_fragment_id=collateral_fragment_id,
            )
        except RequestException as error:
            raise NackException(
                "Error connecting to MediaHaven, retrying....",
                requeue=True,
                error=error,
            )

    def _put_metadata_collateral(self, fragment, event):
        try:
            pid = fragment.Dynamic.PID
            collateral = transform_to_ebucore(event.metadata.raw)

            metadata_dict = {
                "PID": pid,
                "Md5": md5(BytesIO(collateral).getbuffer()).hexdigest(),
                "MEDIA_ID": event.metadata.media_id,
            }
            sidecar = construct_sidecar(metadata_dict)

            dest_filename = f"{pid}_metadata"
            dest_path = f"/vrt/{self.config['ftp']['destination-folder']}"

            self.log.info(
                f"Putting ebucore + sidecar to {dest_path} as {dest_filename}."
            )

            self.ftp_client.put(collateral, dest_path, f"{dest_filename}.ebu")
            self.ftp_client.put(sidecar, dest_path, f"{dest_filename}.xml")
        except Exception as error:
            raise NackException(
                "Failed to upload metadata as collateral.",
                error=error,
                pid=pid,
                metadata=event.metadata.raw,
            )

    def _transform_metadata(self, event):
        try:
            mtd_cfg = self.config["mtd-transformer"]
            url = f"{mtd_cfg['host']}/transform/?transformation={mtd_cfg['transformation']}"
            transformation_response = requests.post(
                url,
                data=event.metadata.raw,
                headers={"Content-Type": "application/xml"},
            )
            transformation_response.raise_for_status()

            self.log.info(
                "Succesfuly transformed metadata using mtd-transformation-service.",
                media_id=event.metadata.media_id,
            )

            return transformation_response.text
        except HTTPError as error:
            raise NackException(
                "Failed to transform metadata using mtd-transformation-service.",
                error=error,
                metadata=event.metadata.raw,
            )
        except RequestException as error:
            raise NackException(
                "Error connecting to mtd-transformation-service, retrying....",
                requeue=True,
                error=error,
            )

    def _update_metadata(self, fragment, metadata):
        try:
            fragment_id = fragment.Internal.FragmentId

            self.log.info(f"Updating metadata in MediaHaven for {fragment_id}")

            self.mediahaven_client.records.update(
                fragment_id,
                metadata=metadata,
                metadata_content_type="application/xml",
                reason="[VRT-events-metadata] Metadata updated",
            )
            time.sleep(SLEEP_TIME)
        except MediaHavenException as error:
            # Invalid metadata update
            raise NackException(
                "Failed to update metadata in MediaHaven.",
                error=error,
                fragment_id=fragment_id,
                metadata=metadata,
            )
        except RequestException as error:
            raise NackException(
                "Error connecting to MediaHaven, retrying....",
                requeue=True,
                error=error,
            )

    def _request_subtitles(self, event):
        if event.media_type == "video" and event.metadata.openOT_available:
            open_ot_request = generate_make_subtitle_available_request_xml(
                "open", event.metadata.media_id, event.metadata.media_id
            )
            self.log.info(
                f"Requesting subtitles for media_id {event.metadata.media_id}"
            )
            self.rabbit_client.send_message(
                self.config["rabbitmq"]["get_subtitles_routing_key"],
                open_ot_request,
                self.config["rabbitmq"]["exchange"],
            )

        if event.media_type == "video" and event.metadata.closedOT_available:
            closed_ot_request = generate_make_subtitle_available_request_xml(
                "closed", event.metadata.media_id, event.metadata.media_id
            )
            self.log.info(
                f"Requesting subtitles for media_id {event.metadata.media_id}"
            )
            self.rabbit_client.send_message(
                self.config["rabbitmq"]["get_subtitles_routing_key"],
                closed_ot_request,
                self.config["rabbitmq"]["exchange"],
            )

    def _handle_nack_exception(self, nack_exception, channel, delivery_tag):
        """Log an error and send a nack to rabbit"""
        self.log.error(nack_exception.message, **nack_exception.kwargs)
        if nack_exception.requeue:
            time.sleep(10)
        channel.basic_nack(delivery_tag=delivery_tag, requeue=nack_exception.requeue)

    def handle_message(self, channel, method, properties, body):
        """Main method that will handle the incoming messages."""
        try:
            event = self._parse_event(method, properties, body)

            # We need all archived items for media id (fragment + collaterals)
            items = self._get_items_for_media_id(event)

            fragment = self._get_fragment(items, event)

            self._delete_existing_metadata_collateral(items, fragment)

            self._put_metadata_collateral(fragment, event)

            metadata = self._transform_metadata(event)

            self._update_metadata(fragment, metadata)

            self._request_subtitles(event)
        except NackException as e:
            self._handle_nack_exception(e, channel, method.delivery_tag)
            return
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        # Start listening for incoming messages
        self.log.info(f"Waiting for messages on queue {self.queue_name}")
        self.rabbit_client.listen(self.handle_message)
