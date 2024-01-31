import time
from typing import Any

import numpy as np
from loguru import logger
from numpy import floating
from numpy.typing import NDArray
from ravelights.audio.ring_buffer import RingBuffer


class FrequencyBandAnalyzer:
    def __init__(
        self,
        start_freq: int,
        end_freq: int,
        chunks_per_second: int,
        energy_seconds: float = 60,
        level_seconds: float = 0.05,
        presence_seconds: float = 15,
    ) -> None:
        self._N_ENERGY_CHUNKS = int(energy_seconds * chunks_per_second)
        self._N_LEVEL_CHUNKS = int(level_seconds * chunks_per_second)
        self._N_PRESENCE_CHUNKS = int(presence_seconds * chunks_per_second)
        self._PERCENTILE_PERCENT = 99

        self._MIN_HIT_TO_MEAN_RATIO = 1.3
        self._MIN_HIT_LEVEL = 0.5
        self._MIN_INTER_HIT_SECONDS = 0.3  # allows to detect hits with up to  200 bpm

        self._start_freq = start_freq
        self._end_freq = end_freq
        self._energies = RingBuffer(capacity=self._N_ENERGY_CHUNKS, dtype=np.float32)
        self._last_hit_seconds = 0.0
        self._level = 0.0
        self._presence = 0.0
        self._is_hit = False

    def analyze(self, spectrum: NDArray[np.complex128], spectrum_frequencies: NDArray[floating[Any]]) -> None:
        band_energy = self._compute_band_energy(spectrum, spectrum_frequencies)
        self._energies.append(band_energy)

        maximum_energy = self._energies.array.max()
        self._level = self._compute_level(maximum_energy=maximum_energy)
        self._presence = self._compute_presence(maximum_energy=maximum_energy)

        self._is_hit = self._detect_hit()

    @property
    def level(self) -> float:
        return self._level

    @property
    def presence(self) -> float:
        return self._presence

    @property
    def is_hit(self) -> bool:
        return self._is_hit

    def _compute_band_energy(
        self, spectrum: NDArray[np.complex128], spectrum_frequencies: NDArray[floating[Any]]
    ) -> float:
        band_spectrum = spectrum[(spectrum_frequencies >= self._start_freq) & (spectrum_frequencies < self._end_freq)]
        band_magnitudes = np.abs(band_spectrum)
        band_energy = np.sum(band_magnitudes**2)
        return float(band_energy)

    def _compute_level(self, maximum_energy: float) -> float:
        if maximum_energy == 0:
            return 0

        percentile = float(np.percentile(self._energies.recent(self._N_LEVEL_CHUNKS), self._PERCENTILE_PERCENT))
        return percentile / maximum_energy

    def _compute_presence(self, maximum_energy: float) -> float:
        if maximum_energy == 0:
            return 0

        percentile = float(np.percentile(self._energies.recent(self._N_PRESENCE_CHUNKS), self._PERCENTILE_PERCENT))
        return percentile / maximum_energy

    def _detect_hit(self) -> bool:
        current_energy = self._energies.recent(1)[0]
        mean_energy = self._energies.array.mean()

        if mean_energy == 0:
            return False

        hit_to_mean_ratio = float((current_energy - mean_energy) / mean_energy)
        current_seconds = time.time()
        seconds_since_last_hit = current_seconds - self._last_hit_seconds

        if all(
            [
                hit_to_mean_ratio >= self._MIN_HIT_TO_MEAN_RATIO,
                self._level >= self._MIN_HIT_LEVEL,
                seconds_since_last_hit >= self._MIN_INTER_HIT_SECONDS,
            ]
        ):
            # Temporarily for  debugging
            if (self._start_freq, self._end_freq) == (0, 200):
                logger.info(f"{hit_to_mean_ratio=}, {self._level=}, {seconds_since_last_hit=}")

            self._last_hit_seconds = current_seconds
            return True

        return False
