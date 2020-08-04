#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import uuid
from datetime import datetime

import requests
from pika.exceptions import AMQPConnectionError
from requests.exceptions import HTTPError, RequestException
from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.helpers.events_parser import EventParser
from app.helpers.xml_helper import transform_to_ebucore
from app.services.mediahaven import MediahavenClient
from app.services.rabbit import RabbitClient
from app.models.exceptions import InvalidEventException


class EventListener:
    def __init__(self):
        configParser = ConfigParser()
        self.log = logging.get_logger(__name__, config=configParser)
        self.config = configParser.app_cfg
        self.mh_client = MediahavenClient(self.config)
        self.event_parser = EventParser()

        try:
            self.rabbit_client = RabbitClient()
        except AMQPConnectionError as error:
            self.log.error("Connection to RabbitMQ failed.")
            raise error

    def handle_message(self, channel, method, properties, body):
        """Main method that will handle the incoming messages.
        """
        # 1. Determine if event is getMetadataResponse or MetadataUpdate
        event_type = method.routing_key.split(".")[-1]

        # 2. Get metadata from event
        try:
            event = self.event_parser.get_event(event_type, body)
        except InvalidEventException as ex:
            self.log.warning("Invalid event received.", body=body, exception=ex)
            # The message body doesn't have the required fields.
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # 3. Check if mediahaven has the object
        try:
            result = self.mh_client.get_fragment(
                "dc_identifier_localid", event.media_id
            )

            fragment_id = result["MediaDataList"][0]["Internal"]["FragmentId"]
            department_id = result["MediaDataList"][0]["Internal"]["DepartmentId"]
            pid = result["MediaDataList"][0]["Administrative"]["ExternalId"]
            self.log.debug(
                "Found fragment id.", fragment_id=fragment_id, media_id=event.media_id
            )
        except RequestException as ex:
            # An error occured when connecting to MH, requeue to try again after 10 secs.
            time.sleep(10)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return
        except IndexError as ex:
            self.log.info(
                "Fragment not found in MH", media_id=event.media_id, exception=ex
            )
            # Fragment is not found in MH
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # 4. Save ebucore metadata as colleteral
        try:
            external_id = f"{pid}_metadata"
            file = transform_to_ebucore(event.metadata.raw)
            self.mh_client.upload_file(file, pid, external_id, department_id)
        except Exception:
            self.log.info("Failed to upload metadata as collateral")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        # 5. Call mtd-transformation-service
        try:
            mtd_cfg = self.config["mtd-transformer"]
            url = f"{mtd_cfg['host']}/transform/?transformation={mtd_cfg['transformation']}"
            transformation_response = requests.post(
                url,
                data=event.metadata.raw,
                headers={"Content-Type": "application/xml"},
            )
            transformation_response.raise_for_status()
        except HTTPError as ex:
            self.log.info(
                "Failed to transform metadata in the sidecar format.",
                metadata=event.metadata.raw,
                exception=ex,
            )
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        except RequestException as ex:
            # An error occured when connecting to MTD-transfo, requeue to try again after 10 secs.
            time.sleep(10)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        # 6. Update mediahaven fragement with received metadata
        try:
            self.mh_client.update_metadata(fragment_id, transformation_response.text)
        except HTTPError as ex:
            # Invalid metadata update
            self.log.error(
                "Error while updating metadata.", error=ex, fragment_id=fragment_id
            )
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        except RequestException as ex:
            # An error occured when connecting to MH, requeue to try again after 10 secs.
            time.sleep(10)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        # Start listening for incoming messages
        self.rabbit_client.listen(self.handle_message)
