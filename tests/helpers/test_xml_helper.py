from app.helpers.xml_helper import (
    generate_make_subtitle_available_request_xml,
)
from tests.resources import resources


def test_construct_subtitle_request():
    # ARRANGE
    ot_type = "open"
    correlation_id = "correlationId"
    media_id = "mediaId"
    ref_xml = resources.load_xml_resource("makeSubtitleAvailableRequest")

    # ACT
    test_xml = generate_make_subtitle_available_request_xml(
        ot_type, correlation_id, media_id
    )

    # ASSERT
    assert ref_xml == test_xml
