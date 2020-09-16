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
        "Md5": "a1b2c3d4e5f6"
    }
    ref_xml = b"<?xml version='1.0' encoding='UTF-8'?>\n<MediaHAVEN_external_metadata>\n  <title>Collateral: pid: abc123</title>\n  <description>Metadata for essence:\n    - PID: abc123\n    - CP: VRT\n    </description>\n  <MDProperties>\n    <CP>VRT</CP>\n    <CP_id>OR-rf5kf25</CP_id>\n    <sp_name>s3</sp_name>\n    <PID>abc123_metadata</PID>\n    <md5>a1b2c3d4e5f6</md5>\n    <dc_relations>\n      <is_verwant_aan>abc123</is_verwant_aan>\n    </dc_relations>\n  </MDProperties>\n</MediaHAVEN_external_metadata>\n"

    # ACT
    test_xml = construct_sidecar(metadata_dict)

    # ASSERT
    assert ref_xml == test_xml
