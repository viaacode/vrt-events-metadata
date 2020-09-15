#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import uuid
from datetime import datetime
from io import BytesIO
from hashlib import md5

import requests
from pika.exceptions import AMQPConnectionError
from requests.exceptions import HTTPError, RequestException
from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.helpers.events_parser import EventParser
from app.helpers.xml_helper import transform_to_ebucore, construct_sidecar
from app.services.mediahaven import MediahavenClient
from app.services.rabbit import RabbitClient
from app.services.ftp import FTPClient
from app.models.exceptions import InvalidEventException


class NackException(Exception):
    """ Exception raised when there is a situation in which handling
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
        self.mh_client = MediahavenClient(configParser)
        self.event_parser = EventParser()

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
                "Unable to parse the incoming event", error=error, body=body,
            )

        return event

    def _get_items_for_media_id(self, event):
        try:
            result = self.mh_client.get_fragment(
                "dc_identifier_localid", event.metadata.media_id
            )
        except RequestException as error:
            raise NackException(
                "Error connecting to MediaHaven, retrying....",
                error=error,
                requeue=True,
            )

        if result["TotalNrOfResults"] == 0:
            raise NackException(
                "Nothing found in MH for media id", media_id=event.metadata.media_id,
            )

        return result["MediaDataList"]

    def _get_fragment(self, items):
        try:
            fragment = next(filter(lambda item: item["Internal"]["IsFragment"], items))

            return fragment
        except StopIteration:
            raise NackException(
                "Fragment not found in MH for media id",
                media_id=event.metadata.media_id,
            )

    def _delete_existing_metadata_collateral(self, items, fragment):
        try:
            fragment_pid = fragment["Dynamic"]["PID"]

            collateral = next(
                filter(
                    lambda item: item["Administrative"]["ExternalId"]
                    == f"{fragment_pid}_metadata",
                    result["MediaDataList"],
                )
            )

            collateral_fragment_id = collateral["Internal"]["FragmentId"]

            self.log.info(
                f"Deleting existing metadata collateral for {fragment_pid}.",
                pid=fragment_pid,
                collateral_fragment_id=collateral_fragment_id,
            )

            self.mh_client.delete_fragment(collateral_fragment_id)
        except StopIteration:
            # No existing collateral, do nothing
            pass
        except HTTPError as error:
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

    def _put_metadata_collateral(self, fragment, metadata):
        try:
            pid = fragment["Dynamic"]["PID"]
            collateral = transform_to_ebucore(metadata)

            metadata_dict = {
                "PID": pid,
                "Md5": md5(BytesIO(collateral).getbuffer()).hexdigest(),
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
                metadata=metadata,
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
            fragment_id = fragment["Internal"]["FragmentId"]

            self.log.info(f"Updating metadata in MediaHaven for {fragment_id}")

            self.mh_client.update_metadata(fragment_id, metadata)
        except HTTPError as error:
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

    def _handle_nack_exception(self, nack_exception, channel, delivery_tag):
        """ Log an error and send a nack to rabbit """
        self.log.error(nack_exception.message, **nack_exception.kwargs)
        if nack_exception.requeue:
            time.sleep(10)
        channel.basic_nack(delivery_tag=delivery_tag, requeue=nack_exception.requeue)

    def handle_message(self, channel, method, properties, body):
        """Main method that will handle the incoming messages.
        """
        try:
            event = self._parse_event(method, properties, body)

            # We need all archived items for media id (fragment + collaterals)
            items = self._get_items_for_media_id(event)

            fragment = self._get_fragment(items)

            self._delete_existing_metadata_collateral(items, fragment)

            self._put_metadata_collateral(fragment, event.metadata.raw)

            metadata = self._transform_metadata(event)
        except NackException as e:
            self._handle_nack_exception(e, channel, method.delivery_tag)
            return
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        # Start listening for incoming messages
        self.log.info("Start to listen for incoming metadata events...")
        self.rabbit_client.listen(self.handle_message)
