#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import uuid
from datetime import datetime

import requests
from requests.exceptions import RequestException
from viaa.configuration import ConfigParser
from viaa.observability import logging

from app.helpers.events_parser import (
    InvalidEventException,
    MetadataUpdatedEvent,
    GetMetadataResponse,
)
from app.services.mediahaven import MediahavenClient
from app.services.rabbit import RabbitClient
from pika.exceptions import AMQPConnectionError


class EventListener:
    def __init__(self):
        configParser = ConfigParser()
        self.log = logging.get_logger(__name__, config=configParser)
        self.config = configParser.app_cfg
        self.mh_client = MediahavenClient(self.config)

        try:
            self.rabbit_client = RabbitClient()
        except AMQPConnectionError as error:
            self.log.error("Connection to RabbitMQ failed.")
            raise error

    def handle_message(self, channel, method, properties, body):
        """Main method that will handle the incoming messages.
        """
        # 1. Determine if event is getMetadataResponse or MetadataUpdate
        routing_key = method.routing_key

        # 2. Get metadata from event
        try:
            if routing_key == "event.to.viaa.getMetadataResponse":
                event = GetMetadataResponse(body)
            if routing_key == "event.to.viaa.metadataUpdatedEvent":
                event = MetadataUpdatedEvent(body)
        except InvalidEventException as ex:
            self.log.info("Invalid event received.", event=body, exception=ex)
            # The message body doesn't have the required fields.
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # 3. Check if mediahaven has the object
        try:
            result = self.mh_client.get_fragment(
                "dc_identifier_localid", event.media_id
            )

            fragment_id = result["MediaDataList"][0]["Internal"]["FragmentId"]
            self.log.debug(
                "Found fragment id.", fragment_id=fragment_id, media_id=event.media_id
            )
        except RequestException as ex:
            # An error occured when connecting to MH
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return
        except KeyError as ex:
            self.log.info(
                "Fragment not found in MH", media_id=event.media_id, exception=ex
            )
            # Fragment is not found in MH
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # 4. Call mtd-transformation-service
        try:
            mtd_cfg = self.config["mtd-transformer"]
            url = f"{mtd_cfg['host']}/transform/?transformation={mtd_cfg['transformation']}"
            transformation_response = requests.post(
                url, data=event.metadata, headers={"Content-Type": "application/xml"},
            )
            transformation_response.raise_for_status()
        except RequestException as ex:
            self.log.info(
                "Failed to transform metadata in the sidecar format.",
                metadata=event.metadata,
                exception=ex,
            )
            # Metadata transformation failed.
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # 5. Update mediahaven fragement with received metadata
        try:
            self.mh_client.update_metadata(fragment_id, transformation_response.text)
        except RequestException as ex:
            # An error occured when connecting to MH
            self.log.error("Error while updating metadata.", error=ex, fragment_id=fragment_id)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        channel.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        # Start listening for incoming messages
        self.rabbit_client.listen(self.handle_message)
