import time
from multiprocessing.connection import _ConnectionBase

import numpy as np
from numpy.typing import NDArray
from ravelights.audio.audio_data import DEFAULT_AUDIO_DATA
from ravelights.audio.audio_source import AudioSource
from ravelights.audio.beat_detector import AubioBeatDetector, BeatDetector
from ravelights.audio.frequency_band_analyzer import FrequencyBandAnalyzer
from ravelights.audio.ring_buffer import RingBuffer


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

        self._lows_analyzer = FrequencyBandAnalyzer(
            start_freq=0,
            end_freq=200,
            chunks_per_second=self.audio_source.CHUNKS_PER_SECOND,
        )
        self._mids_analyzer = FrequencyBandAnalyzer(
            start_freq=200,
            end_freq=2000,
            chunks_per_second=self.audio_source.CHUNKS_PER_SECOND,
        )
        self._highs_analyzer = FrequencyBandAnalyzer(
            start_freq=2000,
            end_freq=self.audio_source.SAMPLING_RATE // 2,
            chunks_per_second=self.audio_source.CHUNKS_PER_SECOND,
        )
        self._total_analyzer = FrequencyBandAnalyzer(
            start_freq=0,
            end_freq=self.audio_source.SAMPLING_RATE // 2,
            chunks_per_second=self.audio_source.CHUNKS_PER_SECOND,
        )

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

        # frequency bands
        self._lows_analyzer.analyze(spectrum, self.SPECTRUM_FREQUENCIES)
        self._mids_analyzer.analyze(spectrum, self.SPECTRUM_FREQUENCIES)
        self._highs_analyzer.analyze(spectrum, self.SPECTRUM_FREQUENCIES)
        self._total_analyzer.analyze(spectrum, self.SPECTRUM_FREQUENCIES)

        # level
        self.audio_data["level"] = self._total_analyzer.level
        self.audio_data["level_low"] = self._lows_analyzer.level
        self.audio_data["level_mid"] = self._mids_analyzer.level
        self.audio_data["level_high"] = self._highs_analyzer.level

        # presence
        self.audio_data["presence"] = self._total_analyzer.presence
        self.audio_data["presence_low"] = self._lows_analyzer.presence
        self.audio_data["presence_mid"] = self._mids_analyzer.presence
        self.audio_data["presence_high"] = self._highs_analyzer.presence

        # hits
        self.audio_data["is_hit"] = self._total_analyzer.is_hit
        self.audio_data["is_hit_low"] = self._lows_analyzer.is_hit
        self.audio_data["is_hit_mid"] = self._mids_analyzer.is_hit
        self.audio_data["is_hit_high"] = self._highs_analyzer.is_hit

        # beat
        self.audio_data["is_beat"] = False
        if self.beat_detector is not None:
            beat_time = self.beat_detector.detect_beat(samples)
            if beat_time is not None:
                self.bpm_calculator.register_beat(beat_time)
                self.audio_data["is_beat"] = True

        self.send_audio_data()

    def send_audio_data(self) -> None:
        self.connection.send(self.audio_data)


def audio_analyzer_process(connection: _ConnectionBase) -> None:
    audio_source = AudioSource(sampling_rate=44100, chunk_size=512)
    beat_detector = AubioBeatDetector(sampling_rate=audio_source.SAMPLING_RATE, hop_size=audio_source.CHUNK_SIZE)
    audio_analyzer = AudioAnalyzer(connection, audio_source, beat_detector)
    audio_source.start(callback=audio_analyzer.process_audio_callback)

    while True:
        time.sleep(1)
