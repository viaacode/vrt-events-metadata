#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from lxml import etree

# Constants
NAMESPACES = {"vrt": "http://www.vrt.be/mig/viaa/api"}


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
