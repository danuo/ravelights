import random
import time
from multiprocessing.connection import _ConnectionBase
from typing import TypedDict


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


class AudioAnalyzer:
    audio_data = AudioData(
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

    def process_audio(self, audio):
        pass


def audio_analyzer_process(connection: _ConnectionBase):
    audio_analyzer = AudioAnalyzer()

    while True:
        # send random data at high rate
        audio_data = {
            "random_float": random.random(),
            "random_bool": random.random() > 0.5,
        }

        audio_analyzer.process_audio(audio_data)
        connection.send(audio_analyzer.audio_data)
        time.sleep(1 / 100)
