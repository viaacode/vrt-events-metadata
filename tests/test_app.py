import pytest

from mediahaven.mocks.base_resource import MediaHavenPageObjectJSONMock

from tests.resources import resources
from tests.resources.mocks import mock_rabbit, mock_mediahaven
from app.app import EventListener
from app.helpers.events_parser import EventParser


@pytest.fixture
def event_listener(mock_rabbit, mock_mediahaven):
    """Creates an event listener with mocked rabbit client, MH client and
    FTP client.
    """
    return EventListener()


def test_get_fragment(event_listener):
    # ARRANGE
    json = resources.load_json_resource("mediahaven_response")
    el = EventListener()

    # ACT

    fragment = el._get_fragment(MediaHavenPageObjectJSONMock(json), None)

    # ASSERT
    assert (
        fragment.Internal.FragmentId
        == "4885061ab2e047728558d24411dd44b8d89c983031994cec9d774270fb807f9697c9ac524f1a471da54c731ceac09bb0"
    )


def test_transform_metadata(event_listener):
    # ARRANGE
    xml = resources.load_xml_resource("getMetadataResponse2")
    event_parser = EventParser()
    event = event_parser.get_event("getMetadataResponse", xml)
    el = EventListener()

    # ACT
    transformed_xml = el._transform_metadata(event)

    # ASSERT
    expected_xml = resources.load_xml_resource(
        "mhs_sidecar_getMetadataResponse2"
    ).decode("utf-8")

    assert transformed_xml == expected_xml
