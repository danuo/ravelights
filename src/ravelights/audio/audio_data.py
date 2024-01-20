from multiprocessing.connection import _ConnectionBase
from typing import TYPE_CHECKING, Optional, TypedDict

if TYPE_CHECKING:
    from ravelights import RaveLightsApp


class AudioData(TypedDict):
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


class AudioDataProvider:
    audio_data: Optional[AudioData] = None
    connection: Optional[_ConnectionBase] = None

    def __init__(self, root: "RaveLightsApp"):
        self.root = root

    def set_connection(self, connection: _ConnectionBase) -> None:
        self.connection = connection

    def collect_audio_data(self) -> None:
        if self.connection is None:
            return

        # all data in the pipe until pipe is empty
        self.data: list[AudioData] = []
        while self.connection.poll():
            self.data.append(self.connection.recv())

        if self.data:
            self.audio_data = self.data[-1]

        # process data
        # print(f"receiving at fps rate {self.data}")
