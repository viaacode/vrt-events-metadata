import pytest

from lxml import etree
from app.helpers.xml_helper import transform_to_ebucore, construct_sidecar
from tests.resources import resources


def test_ebucore_transformation():
    # ARRANGE
    xml = resources.load_xml_resource("getMetadataResponse")

    # ACT
    ebu_xml = transform_to_ebucore(xml)

    # ASSERT
    assert b"ebuCoreMain" in ebu_xml

def test_construct_sidecar():
    # ARRANGE
    metadata_dict = {
        "PID": "abc123",
        "Md5": "a1b2c3d4e5f6",
        "MEDIA_ID": "media-id",
    }
    ref_xml = resources.load_xml_resource("MHSidecar")

    # ACT
    test_xml = construct_sidecar(metadata_dict)

    # ASSERT
    assert ref_xml == test_xml
