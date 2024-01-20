from multiprocessing.connection import _ConnectionBase
from typing import TYPE_CHECKING, Optional

from ravelights.audio.audio_analyzer_process import AudioData

if TYPE_CHECKING:
    from ravelights import RaveLightsApp


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

        self.audio_data = self.data[-1]

        # process data
        print(f"receiving at fps rate {self.data}")
