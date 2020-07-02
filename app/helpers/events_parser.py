#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from lxml import etree

# Constants
NAMESPACES = {
    "vrt": "http://www.vrt.be/mig/viaa/api",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ebu": "urn:ebu:metadata-schema:ebuCore_2012",
}


class InvalidEventException(Exception):
    def __init__(self, message, **kwargs):
        self.message = message
        self.kwargs = kwargs


class Event(object):
    """The base Event object."""

    def __init__(self, xml):
        self.event = self._get_event(xml)
        self._validate_metadata()
        self.timestamp = self._get_xpath_from_event("./vrt:timestamp")
        self.metadata = self._get_xpath_from_event("./vrt:metadata", xml=True)

    def _get_xpath_from_event(self, xpath, xml=False, default: str = None) -> str:
        try:
            if xml:
                return etree.tostring(
                    self.event.xpath(xpath, namespaces=NAMESPACES)[0]
                ).decode("utf-8")
            else:
                return self.event.xpath(xpath, namespaces=NAMESPACES)[0].text
        except IndexError:
            if default is not None:
                return default
            else:
                raise InvalidEventException(f"'{xpath}' is not present in the event.")

    def _validate_metadata(self):
        # Mandatory variables = message is invalid
        framerate = int(
            self._get_xpath_from_event(
                "(//ebu:format[@formatDefinition='current'])[1]/ebu:videoFormat/ebu:frameRate"
            )
        )
        som = self._get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:technicalAttributeString[@typeDefinition='SOM']"
        )
        duration = self._get_xpath_from_event(
            "//ebu:description[@typeDefinition='duration']/dc:description"
        )

        # Optional = set default value
        soc = self._get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:start/ebu:timecode",
            default="00:00:00:00",
        )
        eoc = self._get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:end/ebu:timecode",
            default=duration,
        )
        eom = self._get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:technicalAttributeString[@typeDefinition='EOM']",
            default=duration,
        )

        timecodes = [
            self.__timecode_to_frames(timecode, framerate)
            for timecode in [som, soc, eoc, eom]
        ]

        if timecodes != sorted(timecodes):
            raise InvalidEventException(
                f"Something is wrong with the SOM, SOC, EOC, EOM order."
            )

        if bool(
            self._get_xpath_from_event(
                "(//ebu:format[@formatDefinition='current'])[1]/ebu:start/ebu:timecode",
                default=0,
            )
        ) ^ bool(
            self._get_xpath_from_event(
                "(//ebu:format[@formatDefinition='current'])[1]/ebu:end/ebu:timecode",
                default=0,
            )
        ):
            raise InvalidEventException(
                f"Only SOC or EOC is present. They should both be present or none at all."
            )

    def __timecode_to_frames(self, timecode, framerate):
        try:
            hours, minutes, seconds, frames = [
                int(part) for part in timecode.split(":")
            ]
        except (TypeError, AttributeError, ValueError) as error:
            raise InvalidEventException(
                f"Invalid timecode in the event.", timecode=timecode
            )

        return (hours * 3600 + minutes * 60 + seconds) * framerate + frames


class MetadataUpdatedEvent(Event):
    """Convenience class for an updated metadata Event"""

    def __init__(self, xml):
        super().__init__(xml)
        self.media_id = super()._get_xpath_from_event("./vrt:mediaId")

    def _get_event(self, xml: str):
        """Parse the input XML to a DOM"""
        try:
            tree = etree.parse(BytesIO(xml))
        except etree.XMLSyntaxError:
            raise InvalidEventException("Event is not valid XML.")

        try:
            return tree.xpath(f"/vrt:metadataUpdatedEvent", namespaces=NAMESPACES)[0]
        except IndexError:
            raise InvalidEventException(f"Event is not a 'metadataUpdatedEvent'.")


class GetMetadataResponse(Event):
    """Convenience class for an XML getMetadataResponse Event"""

    def __init__(self, xml):
        super().__init__(xml)
        self.media_id = super()._get_xpath_from_event("./vrt:correlationId")

    def _get_event(self, xml: str):
        """Parse the input XML to a DOM"""
        try:
            tree = etree.parse(BytesIO(xml))
        except etree.XMLSyntaxError:
            raise InvalidEventException("Event is not valid XML.")

        try:
            return tree.xpath(f"/vrt:getMetadataResponse", namespaces=NAMESPACES)[0]
        except IndexError:
            raise InvalidEventException(f"Event is not a 'getMetadataResponse'.")

