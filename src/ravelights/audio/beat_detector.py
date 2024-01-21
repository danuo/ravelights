from abc import ABC, abstractmethod
from typing import Optional

import aubio  # type: ignore
import numpy as np
from numpy.typing import NDArray


class BeatDetector(ABC):
    @abstractmethod
    def detect_beat(self, samples: NDArray[np.float32]) -> Optional[float]:
        """if beat is detected, return time of beat"""
        pass


class AubioBeatDetector(BeatDetector):
    def __init__(self, sampling_rate: int, hop_size: int):
        self._beat_detector = aubio.tempo(
            method="default",
            buf_size=hop_size * 2,
            hop_size=hop_size,
            samplerate=sampling_rate,
        )

    def detect_beat(self, samples: NDArray[np.float32]) -> Optional[float]:
        if self._beat_detector(samples):
            return self._beat_detector.get_last_s()
        return None
