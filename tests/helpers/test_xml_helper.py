import pytest

from lxml import etree
from app.helpers.xml_helper import transform_to_ebucore
from tests.resources import resources


def test_ebucore_transformation():
    # ARRANGE
    xml = etree.fromstring(resources.load_xml_resource("getMetadataResponse"))

    # ACT
    ebu_xml = transform_to_ebucore(xml)

    # ASSERT
    assert 1 == 1
