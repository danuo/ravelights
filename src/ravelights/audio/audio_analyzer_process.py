import random
import time
from multiprocessing.connection import _ConnectionBase
from typing import TypedDict

import numpy as np
import pyaudio

SAMPLE_RATE = 44100
FFT_WINDOW_SIZE = 1024
HOP_SIZE = FFT_WINDOW_SIZE // 2
MEASUREMENTS_PER_SECOND = SAMPLE_RATE // HOP_SIZE
BANDS = [200, 2000]


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

    lows_energies_queue = np.zeros(shape=MEASUREMENTS_PER_SECOND)
    mids_energies_queue = np.zeros(shape=MEASUREMENTS_PER_SECOND)
    highs_energies_queue = np.zeros(shape=MEASUREMENTS_PER_SECOND)
    queue_index = 0

    def __init__(self, connection: _ConnectionBase):
        self.connection = connection

    # use this pattern instead of whie True. update with our code:
    def process_audio(self, audio_buffer, frame_count, time_info, status):
        samples = np.frombuffer(audio_buffer, dtype=np.float32)

        audio_fft = np.fft.fft(samples)
        frequencies = np.fft.fftfreq(HOP_SIZE, 1 / SAMPLE_RATE)

        self.lows_energies_queue[self.queue_index] = self.compute_band_energy(audio_fft, frequencies, 0, BANDS[0])
        self.mids_energies_queue[self.queue_index] = self.compute_band_energy(
            audio_fft, frequencies, BANDS[0], BANDS[1]
        )
        self.highs_energies_queue[self.queue_index] = self.compute_band_energy(
            audio_fft, frequencies, BANDS[1], SAMPLE_RATE // 2
        )

        self.queue_index = (self.queue_index + 1) % MEASUREMENTS_PER_SECOND

        lows_mean = np.array(lows_energies).mean()
        mids_mean = np.array(mids_energies).mean()
        highs_mean = np.array(highs_energies).mean()
        total_mean = lows_energies + mids_energies + highs_energies

        self.send_audio_data()

        return None, pyaudio.paContinue  # Tell pyAudio to continue

    def send_audio_data(self):
        self.connection.send(self.audio_data)

    @staticmethod
    def compute_band_energy(spectrum, frequencies, start_freq, end_freq):
        amplitudes = spectrum[(frequencies >= start_freq) & (frequencies < end_freq)]
        return np.sum(np.abs(amplitudes) ** 2)


def audio_analyzer_process(connection: _ConnectionBase):
    audio_analyzer = AudioAnalyzer(connection)

    stream = pyaudio.PyAudio().open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=HOP_SIZE,
        stream_callback=audio_analyzer.process_audio,
    )
