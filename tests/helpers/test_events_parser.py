import pytest
from app.models.event import Event
from app.models.metadata import Metadata
from app.helpers.events_parser import EventParser
from app.models.exceptions import InvalidEventException


from tests.resources import resources

INVALID_METADATA_RESPONSE_EVENTS = [
    "getMetadataResponseDurationMissing",
    "getMetadataResponseFramerateMissing",
    "getMetadataResponseOnlySoc",
    "getMetadataResponseSocAfterEom",
    "getMetadataResponseSomMissing",
    "getMetadataResponseMalformedTimecode",
    "getMetadataResponseHiresMissing",
    "getMetadataResponseMediaIDMissing",
    "getMetadataResponseInvalidTimecode",
    "getMetadataResponseWrongRootTag",
    "invalidXml",
]

VALID_METADATA_RESPONSE_EVENTS = [
    "getMetadataResponse",
    "getMetadataResponseLoresNodeBeforeHires",
    "getMetadataResponseSOMSOCEOC",
]

VALID_TIMECODES = [
    ("00:00:00:00", 25, 0),
    ("00:00:00:01", 50, 1),
    ("00:00:00:02", 50, 2),
    ("00:00:00:02", 25, 2),
    ("00:00:01:01", 50, 51),
    ("00:01:00:01", 25, 1501),
    ("00:01:00:01", 50, 3001),
    ("01:01:01:01", 25, 91526),
    ("999:01:01:01", 25, 89911526),
]

INVALID_TIMECODES = [
    "00:00:00.00",
    "00:00:00:aa",
    "00:00:aa:02",
    "00:00:100:02",
    "00:100:00:02",
    "-5:00:00:02",
    "01:-03:03:04",
    "Ik heb zin in een zin, maar heeft deze zin wel zin?",
]


@pytest.mark.parametrize("event", VALID_METADATA_RESPONSE_EVENTS)
def test_parse_get_metadata_response(event):
    # ARRANGE
    xml = resources.load_xml_resource(event)
    event_parser = EventParser()

    # ACT
    event = event_parser.get_event("getMetadataResponse", xml)

    # ASSERT
    assert event.metadata.media_id == "TEST_ID"
    assert event.timestamp == "2019-09-24T17:21:28.787+02:00"
    assert event.status == "SUCCESS"
    assert event.correlation_id == "test_correlation"
    assert event.metadata.raw is not None


def test_parse_metadata_updated_event():
    # ARRANGE
    xml = resources.load_xml_resource("metadataUpdatedEvent")
    event_parser = EventParser()

    # ACT
    event = event_parser.get_event("metadataUpdatedEvent", xml)

    # ASSERT
    assert event.metadata.media_id == "TESTJEVANRUDOLF"
    assert event.timestamp == "2019-09-24T17:21:28.787+02:00"
    assert event.media_id == "TESTJEVANRUDOLF"
    assert event.metadata.raw is not None


@pytest.mark.parametrize("event", INVALID_METADATA_RESPONSE_EVENTS)
def test_parse_invalid_get_metadata_response(event):
    # ARRANGE
    xml = resources.load_xml_resource(event)
    event_parser = EventParser()

    # ACT
    with pytest.raises(InvalidEventException):
        event = event_parser.get_event("getMetadataResponse", xml)


@pytest.mark.parametrize("timecode", VALID_TIMECODES)
def test_timecode_to_frames(timecode):
    # ARRANGE
    xml = resources.load_xml_resource("getMetadataResponse")
    event_parser = EventParser()
    event = event_parser.get_event("getMetadataResponse", xml)

    # ACT
    frames = event.metadata._Metadata__timecode_to_frames(timecode[0], timecode[1])

    # ASSERT
    assert frames == timecode[2]


@pytest.mark.parametrize("timecode", INVALID_TIMECODES)
def test_invalid_timecode_to_frames(timecode):
    # ARRANGE
    xml = resources.load_xml_resource("getMetadataResponse")
    event_parser = EventParser()
    event = event_parser.get_event("getMetadataResponse", xml)

    # ACT
    with pytest.raises(InvalidEventException):
        event.metadata._Metadata__timecode_to_frames(timecode[0], timecode[1])

