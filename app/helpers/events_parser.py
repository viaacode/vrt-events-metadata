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


class MetadataUpdatedEvent:
    """Convenience class for an updated metadata Event"""

    def __init__(self, xml):
        self.event = self.__get_event(xml)
        self.timestamp = self.__get_xpath_from_event("./vrt:timestamp")
        self.metadata = self.__get_xpath_from_event("./vrt:metadata", xml=True)
        self.media_id = self.__get_xpath_from_event("./vrt:mediaId")

    def __get_event(self, xml: str):
        """Parse the input XML to a DOM"""
        try:
            tree = etree.parse(BytesIO(xml))
        except etree.XMLSyntaxError:
            raise InvalidEventException("Event is not valid XML.")

        try:
            return tree.xpath("/vrt:metadataUpdatedEvent", namespaces=NAMESPACES)[0]
        except IndexError:
            raise InvalidEventException("Event is not a 'metadataUpdatedEvent'.")

    def __get_xpath_from_event(self, xpath, xml=False) -> str:
        try:
            if xml:
                return etree.tostring(
                    self.event.xpath(xpath, namespaces=NAMESPACES)[0]
                ).decode("utf-8")
            else:
                return self.event.xpath(xpath, namespaces=NAMESPACES)[0].text

        except IndexError:
            raise InvalidEventException(f"'{xpath}' is not present in the event.")


class GetMetadataResponse:
    """Convenience class for an XML getMetadataResponse Event"""

    def __init__(self, xml):
        self.event = self.__get_event(xml)
        self.__validate_metadata()
        self.timestamp = self.__get_xpath_from_event("./vrt:timestamp")
        self.metadata = self.__get_xpath_from_event("./vrt:metadata", xml=True)
        self.media_id = self.__get_xpath_from_event("./vrt:correlationId")

    def __get_event(self, xml: str):
        """Parse the input XML to a DOM"""
        try:
            tree = etree.parse(BytesIO(xml))
        except etree.XMLSyntaxError:
            raise InvalidEventException("Event is not valid XML.")

        try:
            return tree.xpath("/vrt:getMetadataResponse", namespaces=NAMESPACES)[0]
        except IndexError:
            raise InvalidEventException("Event is not a 'GetMetadataResponse'.")

    def __get_xpath_from_event(self, xpath, xml=False, default: str = None) -> str:
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

    def __validate_metadata(self):
        # Mandatory variables = message is invalid
        framerate = int(
            self.__get_xpath_from_event(
                "(//ebu:format[@formatDefinition='current'])[1]/ebu:videoFormat/ebu:frameRate"
            )
        )
        som = self.__get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:technicalAttributeString[@typeDefinition='SOM']"
        )
        duration = self.__get_xpath_from_event(
            "//ebu:description[@typeDefinition='duration']/dc:description"
        )

        # Optional = set default value
        soc = self.__get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:start/ebu:timecode",
            default="00:00:00:00",
        )
        eoc = self.__get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:end/ebu:timecode",
            default=duration,
        )
        eom = self.__get_xpath_from_event(
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

        if bool(self.__get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:start/ebu:timecode",
            default=0,
        )) ^ bool(self.__get_xpath_from_event(
            "(//ebu:format[@formatDefinition='current'])[1]/ebu:end/ebu:timecode",
            default=0,
        )):
            raise InvalidEventException(
                f"Only SOC or EOC is present. They should both be present or none at all."
            )

    def __timecode_to_frames(self, timecode, framerate):
        hours, minutes, seconds, frames = [int(part) for part in timecode.split(":")]

        return (hours * 3600 + minutes * 60 + seconds) * framerate + frames
