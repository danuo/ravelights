from multiprocessing.connection import _ConnectionBase
from typing import TYPE_CHECKING, Optional, TypedDict

if TYPE_CHECKING:
    from ravelights import RaveLightsApp


class AudioData(TypedDict):
    rms: float

    level: float
    level_low: float
    level_mid: float
    level_high: float

    hits: float
    hits_low: float
    hits_mid: float
    hits_high: float

    presence: float
    presence_low: float
    presence_mid: float
    presence_high: float

    FadeInOut: float
    is_beat: bool


DEFAULT_AUDIO_DATA = AudioData(
    rms=0,
    level=0,
    level_low=0,
    level_mid=0,
    level_high=0,
    hits=0,
    hits_low=0,
    hits_mid=0,
    hits_high=0,
    presence=0,
    presence_low=0,
    presence_mid=0,
    presence_high=0,
    FadeInOut=0,
    is_beat=False,
)


class AudioDataProvider:
    audio_data: AudioData = DEFAULT_AUDIO_DATA.copy()
    connection: Optional[_ConnectionBase] = None

    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.received_data: list[AudioData] = []

    def set_connection(self, connection: _ConnectionBase) -> None:
        self.connection = connection

    def collect_audio_data(self) -> None:
        if self.connection is None:
            return

        # all data in the pipe until pipe is empty
        while self.connection.poll():
            self.received_data.append(self.connection.recv())

        if self.received_data:
            self.audio_data = self.received_data[-1]
            for data in self.received_data:
                if data["is_beat"]:
                    self.audio_data["is_beat"] = True
        self.received_data.clear()
