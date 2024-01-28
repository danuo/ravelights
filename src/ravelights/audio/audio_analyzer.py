import time
from dataclasses import dataclass
from multiprocessing.connection import _ConnectionBase

import numpy as np
from numpy.typing import NDArray
from ravelights.audio.audio_data import DEFAULT_AUDIO_DATA
from ravelights.audio.audio_source import AudioSource
from ravelights.audio.beat_detector import AubioBeatDetector, BeatDetector
from ravelights.audio.ring_buffer import RingBuffer


@dataclass
class BandData:
    energies: RingBuffer
    last_hit_seconds = 0.0
    level = 0.0


class BpmCalculator:
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
        self.bpm_calculator = BpmCalculator()
        self.beat_detector = beat_detector

        self.FFT_WINDOW_SIZE = audio_source.CHUNK_SIZE * 2
        self.SPECTRUM_FREQUENCIES = np.fft.fftfreq(self.FFT_WINDOW_SIZE, 1 / self.audio_source.SAMPLING_RATE)
        self.samples = RingBuffer(capacity=self.FFT_WINDOW_SIZE, dtype=np.float32)

        self.CACHE_SECONDS = 60
        self.N_CACHED_CHUNKS = self.CACHE_SECONDS * self.audio_source.CHUNKS_PER_SECOND
        self.lows_data = BandData(energies=RingBuffer(capacity=self.N_CACHED_CHUNKS, dtype=np.float32))
        self.mids_data = BandData(energies=RingBuffer(capacity=self.N_CACHED_CHUNKS, dtype=np.float32))
        self.highs_data = BandData(energies=RingBuffer(capacity=self.N_CACHED_CHUNKS, dtype=np.float32))
        self.total_data = BandData(energies=RingBuffer(capacity=self.N_CACHED_CHUNKS, dtype=np.float32))

        self.LEVEL_SECONDS = 0.05
        self.N_LEVEL_CHUNKS = int(self.LEVEL_SECONDS * self.audio_source.CHUNKS_PER_SECOND)
        self.PRESENCE_SECONDS = 5
        self.N_PRESENCE_CHUNKS = int(self.PRESENCE_SECONDS * self.audio_source.CHUNKS_PER_SECOND)
        self.PERCENTILE_PERCENT = 99

        self.MIN_HIT_TO_MEAN_RATIO = 1.3
        self.MIN_HIT_LEVEL = 0.5
        self.MIN_INTER_HIT_SECONDS = 0.3  # allows to detect hits with up to  200 bpm

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

        # s_max
        # range: [0, 1]
        # shape: float
        DECAY_FAST = 0.8
        DECAY_SLOW = 0.97
        s_max = float(np.max(np.abs(samples)))
        s_max_decay_fast = max(self.audio_data["s_max_decay_fast"] * DECAY_FAST, s_max)
        s_max_decay_slow = max(self.audio_data["s_max_decay_slow"] * DECAY_SLOW, s_max)
        self.audio_data["s_max"] = rms
        self.audio_data["s_max_decay_fast"] = s_max_decay_fast
        self.audio_data["s_max_decay_slow"] = s_max_decay_slow

        # energies
        low_energy = self.compute_band_energy(spectrum, (0, 200))
        mid_energy = self.compute_band_energy(spectrum, (200, 2000))
        high_energy = self.compute_band_energy(spectrum, (2000, self.audio_source.SAMPLING_RATE // 2))
        total_energy = self.compute_band_energy(spectrum, (0, self.audio_source.SAMPLING_RATE // 2))

        self.lows_data.energies.append(low_energy)
        self.mids_data.energies.append(mid_energy)
        self.highs_data.energies.append(high_energy)
        self.total_data.energies.append(total_energy)

        # level
        self.audio_data["level"] = self.total_data.level = self.compute_level(self.total_data)
        self.audio_data["level_low"] = self.lows_data.level = self.compute_level(self.lows_data)
        self.audio_data["level_mid"] = self.mids_data.level = self.compute_level(self.mids_data)
        self.audio_data["level_high"] = self.highs_data.level = self.compute_level(self.highs_data)

        # presence
        self.audio_data["presence"] = self.compute_presence(self.total_data)
        self.audio_data["presence_low"] = self.compute_presence(self.lows_data)
        self.audio_data["presence_mid"] = self.compute_presence(self.mids_data)
        self.audio_data["presence_high"] = self.compute_presence(self.highs_data)

        # hits
        self.audio_data["hits"] = self.detect_hit(self.total_data)
        self.audio_data["hits_low"] = self.detect_hit(self.lows_data)
        self.audio_data["hits_mid"] = self.detect_hit(self.mids_data)
        self.audio_data["hits_high"] = self.detect_hit(self.highs_data)

        # beat
        #        self.audio_data["is_beat"] = False
        #        if self.beat_detector is not None:
        #            beat_time = self.beat_detector.detect_beat(samples)
        #            if beat_time is not None:
        #                self.bpm_calculator.register_beat(beat_time)
        #                self.audio_data["is_beat"] = True
        #
        self.audio_data["is_beat"] = self.audio_data["hits_low"]

        self.send_audio_data()

    def send_audio_data(self) -> None:
        self.connection.send(self.audio_data)

    def compute_band_energy(self, spectrum: NDArray[np.complex128], band: tuple[int, int]) -> float:
        band_start, band_end = band
        band_spectrum = spectrum[(self.SPECTRUM_FREQUENCIES >= band_start) & (self.SPECTRUM_FREQUENCIES < band_end)]
        band_magnitudes = np.abs(band_spectrum)
        band_energy = np.sum(band_magnitudes**2)
        return float(band_energy)

    def compute_level(self, band_data: BandData) -> float:
        maximum_energy = band_data.energies.array.max()

        if maximum_energy == 0:
            return 0

        percentile = float(np.percentile(band_data.energies.recent(self.N_LEVEL_CHUNKS), self.PERCENTILE_PERCENT))
        return percentile / maximum_energy

    def compute_presence(self, band_data: BandData) -> float:
        maximum_energy = band_data.energies.array.max()

        if maximum_energy == 0:
            return 0

        percentile = float(np.percentile(band_data.energies.recent(self.N_PRESENCE_CHUNKS), self.PERCENTILE_PERCENT))
        return percentile / maximum_energy

    def detect_hit(self, band_data: BandData) -> bool:
        current_energy = band_data.energies.recent(1)
        mean_energy = band_data.energies.array.mean()

        if mean_energy == 0:
            return False

        energy_increase = float((current_energy - mean_energy) / mean_energy)
        current_seconds = time.time()

        if all(
            [
                energy_increase >= self.MIN_HIT_TO_MEAN_RATIO,
                band_data.level >= self.MIN_HIT_LEVEL,
                (current_seconds - band_data.last_hit_seconds) >= self.MIN_INTER_HIT_SECONDS,
            ]
        ):
            print(
                f"{energy_increase=}, level={band_data.level}, time_delta: {current_seconds - band_data.last_hit_seconds}"
            )
            band_data.last_hit_seconds = current_seconds
            return True

        return False


def audio_analyzer_process(connection: _ConnectionBase) -> None:
    audio_source = AudioSource(sampling_rate=44100, chunk_size=512)
    beat_detector = AubioBeatDetector(sampling_rate=audio_source.SAMPLING_RATE, hop_size=audio_source.CHUNK_SIZE)
    audio_analyzer = AudioAnalyzer(connection, audio_source, beat_detector)
    audio_source.start(callback=audio_analyzer.process_audio_callback)

    while True:
        time.sleep(1)
