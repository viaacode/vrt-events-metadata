#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from lxml import etree
from app.models.event import GetMetadataResponseEvent, MetadataUpdatedEvent
from app.models.metadata import VideoMetadata, AudioMetadata
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
        media_type = self._get_media_type()
        metadata = self._parse_metadata(media_type)

        timestamp = self._get_xpath_from_event("./vrt:timestamp")

        if event_type == "getMetadataResponse":
            correlation_id = self._get_xpath_from_event("./vrt:correlationId")
            status = self._get_xpath_from_event("./vrt:status")

            if status == "SUCCESS":
                return GetMetadataResponseEvent(
                    event_type, metadata, timestamp, correlation_id, status, media_type
                )
            else:
                # TODO: report back to VRT
                raise InvalidEventException(
                    f"getMetadataResponse status wasn't 'SUCCES': {status}"
                )

        if event_type == "metadataUpdatedEvent":
            media_id = self._get_xpath_from_event("./vrt:mediaId")

            return MetadataUpdatedEvent(
                event_type, metadata, timestamp, media_id, media_type
            )

        raise InvalidEventException(f"Can't handle '{event_type}' events")

    def _parse_event(self, event_type: str, xml: bytes):
        """Parse the input XML to a DOM"""
        try:
            tree = etree.parse(BytesIO(xml.strip()))
        except etree.XMLSyntaxError:
            raise InvalidEventException("Event is not valid XML.")

        try:
            return tree.xpath(f"/vrt:{event_type}", namespaces=NAMESPACES)[0]
        except IndexError:
            raise InvalidEventException(f"Event is not a '{event_type}'.")

    def _get_media_type(self) -> str:
        is_video = bool(
            self._get_xpath_from_event(
                f"//ebu:format[@formatDefinition='current']/ebu:videoFormat",
                xml=True,
                optional=True,
            )
        )
        is_audio = bool(
            self._get_xpath_from_event(
                f"//ebu:format[@formatDefinition='current']/ebu:audioFormat",
                xml=True,
                optional=True,
            )
        )

        if is_video:
            return "video"
        if is_audio:
            return "audio"

        raise InvalidEventException("Unknown media type.")

    def _calculate_resolution_xpath(self) -> str:
        """ Calculates the XPATH for the resolution information.

        It will use hires information if it is available. Otherwise, use lores information.

        Returns:
            The XPATH for the resolution information.

        Raises:
            InvalidEventException: If no hires and no lores are available.
        """
        resolutions = ("hires", "lores")
        xpath_resolutions = [
            f"//ebu:format[@formatDefinition='current'][./ebu:videoFormat[@videoFormatDefinition='{res}']]"
            for res
            in resolutions
        ]
        for xpath_resolution in xpath_resolutions:
            if self.event.xpath(xpath_resolution, namespaces=NAMESPACES):
                return xpath_resolution
        raise InvalidEventException("No hires/lores information available.")

    def _parse_metadata(self, media_type):
        raw = self._get_xpath_from_event("./vrt:metadata", xml=True)
        media_id = self._get_xpath_from_event(
            "//ebu:identifier[@typeDefinition='MEDIA_ID']/dc:identifier"
        )

        if media_type == "video":
            base_xpath = self._calculate_resolution_xpath()

            framerate = int(
                self._get_xpath_from_event(
                    f"{base_xpath}/ebu:videoFormat/ebu:frameRate"
                )
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
            openOT_available = bool(
                self._get_xpath_from_event(
                    f"//ebu:identifier[@typeDefinition='otIdOpen']",
                    optional=True,
                    xml=True,
                )
            ) or bool(
                self._get_xpath_from_event(
                    f"//ebu:format/ebu:dataFormat/ebu:captioningFormat[@formatDefinition='open']",
                    optional=True,
                    xml=True,
                )
            )

            closedOT_available = bool(
                self._get_xpath_from_event(
                    f"//ebu:identifier[@typeDefinition='otIdClosed']",
                    optional=True,
                    xml=True,
                )
            ) or bool(
                self._get_xpath_from_event(
                    f"//ebu:format/ebu:dataFormat/ebu:captioningFormat[@formatDefinition='closed']",
                    optional=True,
                    xml=True,
                )
            )

            return VideoMetadata(
                raw,
                framerate,
                duration,
                som,
                soc,
                eoc,
                eom,
                media_id,
                openOT_available,
                closedOT_available,
            )
        if media_type == "audio":
            return AudioMetadata(raw, media_id)

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
