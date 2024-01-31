from multiprocessing.connection import _ConnectionBase
from typing import TYPE_CHECKING, Optional, TypedDict

if TYPE_CHECKING:
    from ravelights import RaveLightsApp


class AudioData(TypedDict):
    rms: float
    s_max: float
    s_max_decay_fast: float
    s_max_decay_slow: float

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

    is_hit: bool
    is_hit_low: bool
    is_hit_mid: bool
    is_hit_high: bool


DEFAULT_AUDIO_DATA = AudioData(
    rms=0,
    s_max=0,
    s_max_decay_fast=0,
    s_max_decay_slow=0,
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
    is_hit=False,
    is_hit_low=False,
    is_hit_mid=False,
    is_hit_high=False,
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

        # Poll all data in the pipe until pipe is empty
        while self.connection.poll():
            self.received_data.append(self.connection.recv())

        if not self.received_data:
            return

        self.audio_data = self.received_data[-1]

        for data in self.received_data:
            if data["is_beat"]:
                self.audio_data["is_beat"] = True
            if data["is_hit"]:
                self.audio_data["is_hit"] = True
            if data["is_hit_low"]:
                self.audio_data["is_hit_low"] = True
            if data["is_hit_mid"]:
                self.audio_data["is_hit_mid"] = True
            if data["is_hit_high"]:
                self.audio_data["is_hit_high"] = True

        self.received_data.clear()
