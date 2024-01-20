import aubio
import numpy as np
from numpy.typing import NDArray
from ravelights.audio.beat_detector import BeatDetector


class AubioBeatDetector(BeatDetector):
    def __init__(self, sampling_rate: int, hop_size: int, bpm_window_size: int = 16):
        super().__init__(bpm_window_size=bpm_window_size)
        self._beat_detector = aubio.tempo(
            method="default",
            buf_size=hop_size * 2,
            hop_size=hop_size,
            samplerate=sampling_rate,
        )

    def process_samples(self, samples: NDArray[np.float32]) -> float | None:
        if not self._beat_detector(samples):
            return None

        self._register_beat(time=self._beat_detector.get_last_s())
        bpm = self._compute_bpm()
        if bpm == 0:
            return None
        return bpm
