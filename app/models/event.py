from app.models.metadata import Metadata
from lxml import etree
from abc import ABC

NAMESPACES = {
    "vrt": "http://www.vrt.be/mig/viaa/api",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ebu": "urn:ebu:metadata-schema:ebuCore_2012",
}


class Event(ABC):
    """The base Event object."""

    def __init__(self, event_type: str, metadata, timestamp: str):
        self.event_type = event_type
        self.timestamp = timestamp
        self.metadata = metadata

        # self.event = event

        # self.timestamp = self._get_xpath_from_event("./vrt:timestamp", optional=True)
        # self.media_id = self._get_xpath_from_event(
        #     "/ebu:identifier[@typeDefinition='MEDIA_ID']/dc:identifier"
        # )


class GetMetadataResponseEvent(Event):
    def __init__(
        self,
        event_type: str,
        metadata,
        timestamp: str,
        correlation_id: str,
        status: str,
    ):
        super().__init__(event_type, metadata, timestamp)
        self.correlation_id = correlation_id
        self.status = status


class MetadataUpdatedEvent(Event):
    def __init__(self, event_type: str, metadata, timestamp: str, media_id: str):
        super().__init__(event_type, metadata, timestamp)
        self.media_id = media_id
