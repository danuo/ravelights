from multiprocessing.connection import _ConnectionBase
from typing import Optional, TypedDict


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

    is_beat: bool
    FadeInOut: float


class AudioDataProvider:
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

    is_beat: bool
    FadeInOut: float

    connection: Optional[_ConnectionBase] = None

    def set_connection(self, connection: _ConnectionBase = None):
        self.connection = connection

    def collect_audio_data(self):
        if self.connection is None:
            return

        # all data in the pipe until pipe is empty
        self.data = []
        while self.connection.poll():
            self.data.append(self.connection.recv())

        # process data
        print(f"receiving at fps rate {self.data}")
