import pytest

from app.helpers.events_parser import GetMetadataResponse, MetadataUpdatedEvent
from tests.resources import resources


def test_parse_get_metadata_response():
    # ARRANGE
    xml = resources.load_xml_resource("getMetadataResponse")

    # ACT
    event = GetMetadataResponse(xml)

    # ASSERT
    assert event.media_id == "123"
    assert event.timestamp == "2019-09-24T17:21:28.787+02:00"
    assert not event.metadata == ""


def test_parse_metadata_updated_event():
    # ARRANGE
    xml = resources.load_xml_resource("metadataUpdatedEvent")

    # ACT
    event = MetadataUpdatedEvent(xml)

    # ASSERT
    assert event.media_id == "123"
    assert event.timestamp == "2019-09-24T17:21:28.787+02:00"
    assert not event.metadata == ""
