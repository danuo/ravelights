from abc import ABC, abstractmethod

import numpy as np
from numpy.typing import NDArray
from ravelights.audio.ring_buffer import RingBuffer


class BeatDetector(ABC):
    def __init__(self, bpm_window_size: int = 16):
        self._beat_times = RingBuffer(capacity=bpm_window_size, dtype=np.float32)

    def _register_beat(self, time: float) -> None:
        self._beat_times.append(time)

    def _compute_bpm(self) -> float | None:
        inter_beat_times = np.diff(self._beat_times.array)
        median_inter_beat_time = np.median(inter_beat_times)
        if median_inter_beat_time == 0:
            return None
        return 60 / float(median_inter_beat_time)

    @abstractmethod
    def process_samples(self, samples: NDArray[np.float32]) -> float | None:
        pass
