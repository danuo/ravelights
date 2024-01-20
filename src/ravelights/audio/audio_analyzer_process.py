import time
from multiprocessing.connection import _ConnectionBase
from typing import Any, TypedDict

import numpy as np
from numpy.typing import NDArray
from ravelights.audio.aubio_beat_detector import AubioBeatDetector
from ravelights.audio.audio_source import AudioSource
from ravelights.audio.beat_detector import BeatDetector
from ravelights.audio.ring_buffer import RingBuffer


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

    def __init__(
        self, connection: _ConnectionBase, audio_source: AudioSource, beat_detector: BeatDetector | None = None
    ):
        self.connection = connection
        self.audio_source = audio_source
        self.beat_detector = beat_detector
        self.fft_window_size = audio_source.chunk_size * 2
        self.spectrum_frequencies = np.fft.fftfreq(self.fft_window_size, 1 / self.audio_source.sampling_rate)
        self.samples = RingBuffer(capacity=self.fft_window_size, dtype=np.float32)
        self.lows_energies = RingBuffer(capacity=self.audio_source.measurements_per_second, dtype=np.float64)
        self.mids_energies = RingBuffer(capacity=self.audio_source.measurements_per_second, dtype=np.float64)
        self.highs_energies = RingBuffer(capacity=self.audio_source.measurements_per_second, dtype=np.float64)
        self.all_energies = RingBuffer(capacity=self.audio_source.measurements_per_second, dtype=np.float64)

    def start(self):
        self.audio_source.start(self.process_audio)

    def process_audio(self, samples: NDArray[np.float32]) -> None:
        self.samples.append_all(samples)

        spectrum = np.fft.fft(self.samples.array)

        self.lows_energies.append(self.compute_band_energy(spectrum, (0, 200)))
        self.mids_energies.append(self.compute_band_energy(spectrum, (200, 2000)))
        self.highs_energies.append(self.compute_band_energy(spectrum, (2000, self.audio_source.sampling_rate // 2)))

        lows_mean = self.lows_energies.array.mean()
        mids_mean = self.mids_energies.array.mean()
        highs_mean = self.highs_energies.array.mean()
        all_mean = lows_mean + mids_mean + highs_mean

        print([lows_mean, mids_mean, highs_mean, all_mean])

        if self.beat_detector is not None:
            is_beat, bpm = self.beat_detector.process_samples(samples)
            if is_beat:
                print(f"Beat detected! BPM: {bpm}")

        self.send_audio_data()

    def send_audio_data(self):
        self.connection.send(self.audio_data)

    def compute_band_energy(self, spectrum: NDArray[np.complex128], band: tuple[int, int]) -> float:
        band_start, band_end = band
        band_spectrum = spectrum[(self.spectrum_frequencies >= band_start) & (self.spectrum_frequencies < band_end)]
        band_magnitudes = np.abs(band_spectrum)
        band_energy = np.sum(band_magnitudes**2)
        return float(band_energy)


def audio_analyzer_process(connection: _ConnectionBase):
    source = AudioSource(sampling_rate=44100, chunk_size=512)
    beat_detector = AubioBeatDetector(sampling_rate=source.sampling_rate, hop_size=source.chunk_size)
    audio_analyzer = AudioAnalyzer(connection, source, beat_detector)
    audio_analyzer.start()

    # Keep the process alive
    while True:
        time.sleep(60)
