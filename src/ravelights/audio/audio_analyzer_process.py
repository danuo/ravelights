import time
from multiprocessing.connection import _ConnectionBase

import numpy as np
from numpy.typing import NDArray
from ravelights.audio.aubio_beat_detector import AubioBeatDetector
from ravelights.audio.audio_data import DEFAULT_AUDIO_DATA
from ravelights.audio.audio_source import AudioSource
from ravelights.audio.beat_detector import BeatDetector
from ravelights.audio.ring_buffer import RingBuffer


class AudioAnalyzer:
    audio_data = DEFAULT_AUDIO_DATA.copy()

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
        self.audio_source.start(callback=self.process_audio)

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

        # print([lows_mean, mids_mean, highs_mean, all_mean])

        if self.beat_detector is not None:
            bpm = self.beat_detector.process_samples(samples)
            if bpm is not None:
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
