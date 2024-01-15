from multiprocessing.connection import PipeConnection


class AudioDataProvider:
    def __init__(self, connection: PipeConnection):
        self.connection = connection

    def collect_audio_data(self):
        # all data in the pipe until pipe is empty
        self.data = []
        while self.connection.poll():
            self.data.append(self.connection.recv())

        # process data
        print(f"receiving at fps rate {self.data}")
