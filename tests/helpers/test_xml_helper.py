import pytest

from lxml import etree
from app.helpers.xml_helper import transform_to_ebucore, construct_sidecar, generate_make_subtitle_available_request_xml
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

def test_construct_subtitle_request():
    # ARRANGE
    ot_type = "open"
    correlation_id = "correlationId"
    media_id = "mediaId"
    ref_xml = resources.load_xml_resource("makeSubtitleAvailableRequest")

    # ACT
    test_xml = generate_make_subtitle_available_request_xml(ot_type, correlation_id, media_id)

    # ASSERT
    assert ref_xml == test_xml