from app.models.exceptions import InvalidEventException
from abc import ABC, abstractmethod

NAMESPACES = {
    "vrt": "http://www.vrt.be/mig/viaa/api",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ebu": "urn:ebu:metadata-schema:ebuCore_2012",
}


class Metadata(ABC):
    def __init__(self, raw, media_id):
        self.raw = raw
        self.media_id = media_id

        self._validate_metadata()

    @abstractmethod
    def _validate_metadata(self):
        pass


class VideoMetadata(Metadata):
    def __init__(
        self,
        raw,
        framerate,
        duration,
        som,
        soc,
        eoc,
        eom,
        media_id,
        openOT_available,
        closedOT_available,
    ):
        self.framerate = framerate
        self.duration = duration
        self.som = som
        self.soc = soc
        self.eoc = eoc
        self.eom = eom
        self.openOT_available = openOT_available
        self.closedOT_available = closedOT_available
        super().__init__(raw, media_id)

    def _validate_metadata(self):
        if bool(self.soc) ^ bool(self.eoc):
            raise InvalidEventException(
                "Only SOC or EOC is present. They should both be present or none at all."
            )

        duration_frames = self.__timecode_to_frames(self.duration, self.framerate)
        som_frames = self.__timecode_to_frames(self.som, self.framerate)
        soc_frames = (
            self.__timecode_to_frames(self.soc, self.framerate)
            if self.soc
            else som_frames
        )
        eoc_frames = (
            self.__timecode_to_frames(self.eoc, self.framerate)
            if self.eoc
            else som_frames + duration_frames
        )
        eom_frames = (
            self.__timecode_to_frames(self.eom, self.framerate)
            if self.eom
            else eoc_frames
        )

        timecodes = [som_frames, soc_frames, eoc_frames, eom_frames]

        if timecodes != sorted(timecodes):
            raise InvalidEventException(
                "Something is wrong with the SOM, SOC, EOC, EOM order."
            )

    def __timecode_to_frames(self, timecode: str, framerate: int) -> int:
        try:
            hours, minutes, seconds, frames = [
                int(part) for part in timecode.split(":")
            ]
        except (TypeError, AttributeError, ValueError):
            raise InvalidEventException(
                "Invalid timecode in the event.", timecode=timecode
            )

        return (hours * 3600 + minutes * 60 + seconds) * framerate + frames


class AudioMetadata(Metadata):
    def __init__(self, raw, media_id):
        super().__init__(raw, media_id)

    def _validate_metadata(self):
        pass
