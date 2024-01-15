from multiprocessing.connection import PipeConnection
from typing import Optional


class AudioDataProvider:
    connection: Optional[PipeConnection] = None

    def set_connection(self, connection: PipeConnection = None):
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
