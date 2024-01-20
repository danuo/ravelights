import time
from multiprocessing.connection import _ConnectionBase
from typing import Any, Mapping, TypedDict

import numpy as np
import pyaudio
from numpy.typing import NDArray
from ravelights.audio.ring_buffer import RingBuffer

SAMPLING_RATE = 44100
FFT_WINDOW_SIZE = 1024
FFT_HOP_SIZE = FFT_WINDOW_SIZE // 2
MEASUREMENTS_PER_SECOND = SAMPLING_RATE // FFT_HOP_SIZE
BANDS = [(0, 200), (200, 2000), (2000, SAMPLING_RATE // 2)]


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

    def __init__(self, connection: _ConnectionBase):
        self.connection = connection
        self.samples = RingBuffer(capacity=FFT_WINDOW_SIZE, dtype=np.float32)
        self.lows_energies = RingBuffer(capacity=MEASUREMENTS_PER_SECOND, dtype=np.float64)
        self.mids_energies = RingBuffer(capacity=MEASUREMENTS_PER_SECOND, dtype=np.float64)
        self.highs_energies = RingBuffer(capacity=MEASUREMENTS_PER_SECOND, dtype=np.float64)
        self.all_energies = RingBuffer(capacity=MEASUREMENTS_PER_SECOND, dtype=np.float64)
        self.last_log_seconds = time.time()

    def process_audio(self, audio_buffer: bytes | None, frame_count: int, time_info: Mapping[str, float], status: int):
        if audio_buffer is None:
            return None, pyaudio.paContinue

        samples = np.frombuffer(audio_buffer, dtype=np.float32)
        self.samples.append_all(samples)

        spectrum = np.fft.fft(self.samples.array)
        spectrum_frequencies = np.fft.fftfreq(FFT_WINDOW_SIZE, 1 / SAMPLING_RATE)

        self.lows_energies.append(self.compute_band_energy(spectrum, spectrum_frequencies, BANDS[0]))
        self.mids_energies.append(self.compute_band_energy(spectrum, spectrum_frequencies, BANDS[1]))
        self.highs_energies.append(self.compute_band_energy(spectrum, spectrum_frequencies, BANDS[2]))

        lows_mean = self.lows_energies.array.mean()
        mids_mean = self.mids_energies.array.mean()
        highs_mean = self.highs_energies.array.mean()
        all_mean = lows_mean + mids_mean + highs_mean

        print([lows_mean, mids_mean, highs_mean, all_mean])

        return None, pyaudio.paContinue  # Tell pyAudio to continue

    def send_audio_data(self):
        self.connection.send(self.audio_data)

    @staticmethod
    def compute_band_energy(
        spectrum: NDArray[np.complex128], spectrum_frequencies: NDArray[np.floating[Any]], band: tuple[int, int]
    ) -> float:
        band_start, band_end = band
        band_spectrum = spectrum[(spectrum_frequencies >= band_start) & (spectrum_frequencies < band_end)]
        band_magnitudes = np.abs(band_spectrum)
        band_energy = np.sum(band_magnitudes**2)
        return float(band_energy)


def audio_analyzer_process(connection: _ConnectionBase):
    audio_analyzer = AudioAnalyzer(connection)

    stream = pyaudio.PyAudio().open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=SAMPLING_RATE,
        input=True,
        frames_per_buffer=FFT_HOP_SIZE,
        stream_callback=audio_analyzer.process_audio,
    )
