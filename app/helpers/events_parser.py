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

    def _validate_metadata(self):
        framerate = int(
            self._get_xpath_from_event(
                "(//ebu:format[@formatDefinition='current'])[1]/ebu:videoFormat/ebu:frameRate"
            )
        )
        duration = self._get_xpath_from_event(
            "//ebu:description[@typeDefinition='duration']/dc:description"
        )
        som = self._get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:technicalAttributeString[@typeDefinition='SOM']"
        )
        soc = self._get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:start/ebu:timecode",
            optional=True,
        )
        eoc = self._get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:end/ebu:timecode",
            optional=True,
        )
        eom = self._get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:technicalAttributeString[@typeDefinition='EOM']",
            optional=True,
        )

        if bool(soc) ^ bool(eoc):
            raise InvalidEventException(
                f"Only SOC or EOC is present. They should both be present or none at all."
            )

        duration_frames = self.__timecode_to_frames(duration, framerate)
        som_frames = self.__timecode_to_frames(som, framerate)
        soc_frames = self.__timecode_to_frames(soc, framerate) if soc else som_frames
        eoc_frames = (
            self.__timecode_to_frames(eoc, framerate)
            if eoc
            else som_frames + duration_frames
        )
        eom_frames = (
            self.__timecode_to_frames(eom, framerate)
            if eom
            else som_frames + duration_frames
        )

        timecodes = [som_frames, soc_frames, eoc_frames, eom_frames]

        if timecodes != sorted(timecodes):
            raise InvalidEventException(
                f"Something is wrong with the SOM, SOC, EOC, EOM order."
            )

    def __timecode_to_frames(self, timecode: str, framerate: int) -> int:
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

