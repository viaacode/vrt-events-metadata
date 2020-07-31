#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from lxml import etree
from app.models.event import GetMetadataResponseEvent, MetadataUpdatedEvent
from app.models.metadata import Metadata
from app.models.exceptions import InvalidEventException

# Constants
NAMESPACES = {
    "vrt": "http://www.vrt.be/mig/viaa/api",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ebu": "urn:ebu:metadata-schema:ebuCore_2012",
}


class EventParser(object):
    def get_event(self, event_type: str, xml: bytes):
        self.event = self._parse_event(event_type, xml)
        metadata = self._parse_metadata()

        timestamp = self._get_xpath_from_event("./vrt:timestamp", optional=True)

        if event_type == "getMetadataResponse":
            correlation_id = self._get_xpath_from_event("./vrt:correlationId")
            status = self._get_xpath_from_event("./vrt:status")

            return GetMetadataResponseEvent(
                event_type, metadata, timestamp, correlation_id, status
            )

        if event_type == "metadataUpdatedEvent":
            media_id = self._get_xpath_from_event("./vrt:mediaId")

            return MetadataUpdatedEvent(event_type, metadata, timestamp, media_id)

        raise InvalidEventException(f"Can't handle '{event_type}' events")

    def _parse_event(self, event_type: str, xml: bytes):
        """Parse the input XML to a DOM"""
        try:
            tree = etree.parse(BytesIO(xml))
        except etree.XMLSyntaxError:
            raise InvalidEventException("Event is not valid XML.")

        try:
            return tree.xpath(f"/vrt:{event_type}", namespaces=NAMESPACES)[0]
        except IndexError:
            raise InvalidEventException(f"Event is not a '{event_type}'.")

    def _parse_metadata(self):
        raw = self._get_xpath_from_event("./vrt:metadata", xml=True)

        base_xpath = "//ebu:format[@formatDefinition='current'][./ebu:videoFormat[@videoFormatDefinition='hires']]"
        framerate = int(
            self._get_xpath_from_event(f"{base_xpath}/ebu:videoFormat/ebu:frameRate")
        )
        duration = self._get_xpath_from_event(
            "//ebu:description[@typeDefinition='duration']/dc:description"
        )
        som = self._get_xpath_from_event(
            f"{base_xpath}/ebu:technicalAttributeString[@typeDefinition='SOM']"
        )
        soc = self._get_xpath_from_event(
            f"{base_xpath}/ebu:start/ebu:timecode", optional=True,
        )
        eoc = self._get_xpath_from_event(
            f"{base_xpath}/ebu:end/ebu:timecode", optional=True,
        )
        eom = self._get_xpath_from_event(
            f"{base_xpath}/ebu:technicalAttributeString[@typeDefinition='EOM']",
            optional=True,
        )
        media_id = self._get_xpath_from_event(
            "//ebu:identifier[@typeDefinition='MEDIA_ID']/dc:identifier"
        )

        return Metadata(raw, framerate, duration, som, soc, eoc, eom, media_id)

    def _get_xpath_from_event(self, xpath, xml=False, optional: bool = False) -> str:
        try:
            if xml:
                return etree.tostring(
                    self.event.xpath(xpath, namespaces=NAMESPACES)[0]
                ).decode("utf-8")
            else:
                return self.event.xpath(xpath, namespaces=NAMESPACES)[0].text
        except IndexError:
            if optional:
                return ""
            else:
                raise InvalidEventException(f"'{xpath}' is not present in the event.")

