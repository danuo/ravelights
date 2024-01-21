import time
from multiprocessing.connection import _ConnectionBase

import numpy as np
from numpy.typing import NDArray
from ravelights.audio.audio_data import DEFAULT_AUDIO_DATA
from ravelights.audio.audio_source import AudioSource
from ravelights.audio.beat_detector import AubioBeatDetector, BeatDetector
from ravelights.audio.ring_buffer import RingBuffer


class BpmCaluclator:
    def __init__(self, bpm_window_size: int = 16):
        self._beat_times = RingBuffer(capacity=bpm_window_size, dtype=np.float32)

    def register_beat(self, time: float) -> None:
        self._beat_times.append(time)

    def _compute_bpm(self) -> float | None:
        inter_beat_times = np.diff(self._beat_times.array)
        median_inter_beat_time = np.median(inter_beat_times)
        if median_inter_beat_time == 0:
            return None
        return 60 / float(median_inter_beat_time)


class AudioAnalyzer:
    audio_data = DEFAULT_AUDIO_DATA.copy()

    def __init__(
        self, connection: _ConnectionBase, audio_source: AudioSource, beat_detector: BeatDetector | None = None
    ):
        self.connection = connection
        self.audio_source = audio_source
        self.bpm_calculator = BpmCaluclator()
        self.beat_detector = beat_detector
        self.FFT_WINDOW_SIZE = audio_source.CHUNK_SIZE * 2
        self.SPECTRUM_FREQUENCIES = np.fft.fftfreq(self.FFT_WINDOW_SIZE, 1 / self.audio_source.SAMPLING_RATE)
        self.samples = RingBuffer(capacity=self.FFT_WINDOW_SIZE, dtype=np.float32)
        self.CACHE_SECONDS = 60
        self.N_CACHED_CHUNKS = self.CACHE_SECONDS * self.audio_source.CHUNKS_PER_SECOND
        self.lows_energies = RingBuffer(capacity=self.N_CACHED_CHUNKS, dtype=np.float64)
        self.mids_energies = RingBuffer(capacity=self.N_CACHED_CHUNKS, dtype=np.float64)
        self.highs_energies = RingBuffer(capacity=self.N_CACHED_CHUNKS, dtype=np.float64)
        self.total_energies = RingBuffer(capacity=self.N_CACHED_CHUNKS, dtype=np.float64)
        self.LEVEL_SECONDS = 0.2
        self.N_LEVEL_CHUNKS = int(self.LEVEL_SECONDS * self.audio_source.CHUNKS_PER_SECOND)
        self.PRESENCE_SECONDS = 5
        self.N_PRESENCE_CHUNKS = int(self.PRESENCE_SECONDS * self.audio_source.CHUNKS_PER_SECOND)

    def process_audio_callback(self, samples: NDArray[np.float32]) -> None:
        # samples
        # range: [-1, 1]
        # shape: (512,)
        self.samples.append_all(samples)
        spectrum = np.fft.fft(self.samples.array)

        # rms
        # range: [0, 1]
        # shape: float
        rms = float(np.sqrt(np.mean(samples**2)))
        self.audio_data["rms"] = rms

        # energies
        low_energy = self.compute_band_energy(spectrum, (0, 200))
        mid_energy = self.compute_band_energy(spectrum, (200, 2000))
        high_energy = self.compute_band_energy(spectrum, (2000, self.audio_source.SAMPLING_RATE // 2))
        total_energy = self.compute_band_energy(spectrum, (0, self.audio_source.SAMPLING_RATE // 2))

        self.lows_energies.append(low_energy)
        self.mids_energies.append(mid_energy)
        self.highs_energies.append(high_energy)
        self.total_energies.append(total_energy)

        # level and presence
        lows_max = self.lows_energies.array.max()
        mids_max = self.mids_energies.array.max()
        highs_max = self.highs_energies.array.max()
        total_max = self.total_energies.array.max()

        if lows_max > 0:
            self.audio_data["level_low"] = float(
                self.lows_energies.recent(self.N_LEVEL_CHUNKS).mean() / self.lows_energies.array.max()
            )
            self.audio_data["presence_low"] = float(
                self.lows_energies.recent(self.N_PRESENCE_CHUNKS).mean() / self.lows_energies.array.max()
            )

        if mids_max > 0:
            self.audio_data["level_mid"] = float(
                self.mids_energies.recent(self.N_LEVEL_CHUNKS).mean() / self.mids_energies.array.max()
            )
            self.audio_data["presence_mid"] = float(
                self.mids_energies.recent(self.N_PRESENCE_CHUNKS).mean() / self.mids_energies.array.max()
            )

        if highs_max > 0:
            self.audio_data["level_high"] = float(
                self.highs_energies.recent(self.N_LEVEL_CHUNKS).mean() / self.highs_energies.array.max()
            )
            self.audio_data["presence_high"] = float(
                self.highs_energies.recent(self.N_PRESENCE_CHUNKS).mean() / self.highs_energies.array.max()
            )

        if total_max > 0:
            self.audio_data["level"] = float(
                self.total_energies.recent(self.N_LEVEL_CHUNKS).mean() / self.total_energies.array.max()
            )
            self.audio_data["presence"] = float(
                self.total_energies.recent(self.N_PRESENCE_CHUNKS).mean() / self.total_energies.array.max()
            )

        self.audio_data["is_beat"] = False
        if self.beat_detector:
            beat_time = self.beat_detector.detect_beat(samples)
            if beat_time:
                self.audio_data["is_beat"] = True
                self.bpm_calculator.register_beat(beat_time)
                # todo: use bpm

        self.send_audio_data()

    def send_audio_data(self) -> None:
        self.connection.send(self.audio_data)

    def compute_band_energy(self, spectrum: NDArray[np.complex128], band: tuple[int, int]) -> float:
        band_start, band_end = band
        band_spectrum = spectrum[(self.SPECTRUM_FREQUENCIES >= band_start) & (self.SPECTRUM_FREQUENCIES < band_end)]
        band_magnitudes = np.abs(band_spectrum)
        band_energy = np.sum(band_magnitudes**2)
        return float(band_energy)


def audio_analyzer_process(connection: _ConnectionBase) -> None:
    audio_source = AudioSource(sampling_rate=44100, chunk_size=512)
    beat_detector = AubioBeatDetector(sampling_rate=audio_source.SAMPLING_RATE, hop_size=audio_source.CHUNK_SIZE)
    audio_analyzer = AudioAnalyzer(connection, audio_source, beat_detector)
    audio_source.start(callback=audio_analyzer.process_audio_callback)

    while True:
        time.sleep(1)
