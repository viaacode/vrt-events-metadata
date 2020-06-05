#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO
from lxml import etree

# Constants
NAMESPACES = {"vrt": "http://www.vrt.be/mig/viaa/api"}


class MetadataUpdatedEvent:
    """Convenience class for an XML getMetadataResponse Event"""

    def __init__(self, xml):
        self.event = self.__get_event(xml)
        self.timestamp = self.__get_xpath_from_event("/vrt:timestamp")
        self.metadata = self.__get_xpath_from_event("/vrt:metadata")
        self.media_id = self.__get_xpath_from_event("/vrt:mediaId")

    def __get_event(self, xml: str):
        """Parse the input XML to a DOM"""
        try:
            tree = etree.parse(BytesIO(xml))
        except etree.XMLSyntaxError:
            return None

        try:
            return tree.xpath("/vrt:essenceLinkedEvent", namespaces=NAMESPACES)[0]
        except IndexError:
            return None

    def __get_xpath_from_event(self, xpath) -> str:
        if not self.event:
            return ""

        try:
            return self.event.xpath(xpath, namespaces=NAMESPACES)[0].text
        except IndexError:
            return ""
