import pytest
from unittest.mock import patch, MagicMock

from lxml import etree
from app.helpers.xml_helper import transform_to_ebucore
from tests.resources import resources
from tests.resources.mocks import mock_ftp, mock_rabbit, mock_mediahaven
from app.app import EventListener


@pytest.fixture
def event_listener(mock_ftp, mock_rabbit, mock_mediahaven):
    """ Creates an event listener with mocked rabbit client, MH client and
    FTP client.
    """
    return EventListener()


def test_get_fragment(event_listener):
    # ARRANGE
    json = resources.load_json_resource("mediahaven_response")
    el = EventListener()

    # ACT
    fragment = el._get_fragment(json["MediaDataList"], None)

    # ASSERT
    assert (
        fragment["Internal"]["FragmentId"]
        == "4885061ab2e047728558d24411dd44b8d89c983031994cec9d774270fb807f9697c9ac524f1a471da54c731ceac09bb0"
    )
