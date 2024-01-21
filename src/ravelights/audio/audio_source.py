from typing import Callable, Mapping

import numpy as np
from numpy.typing import NDArray
from pyaudio import PyAudio, paContinue, paFloat32

AudioSourceCallback = Callable[[NDArray[np.float32]], None]


class AudioSource:
    def __init__(self, sampling_rate: int = 44100, chunk_size: int = 512) -> None:
        self._SAMPLING_RATE = sampling_rate
        self._CHUNK_SIZE = chunk_size

        self._pa = PyAudio()
        self._stream = self._pa.open(
            format=paFloat32,
            channels=1,
            rate=sampling_rate,
            input=True,
            frames_per_buffer=chunk_size,
            stream_callback=self._pyaudio_callback,
            start=False,
        )
        self._callback: AudioSourceCallback | None = None

    @property
    def SAMPLING_RATE(self) -> int:
        return self._SAMPLING_RATE

    @property
    def CHUNK_SIZE(self) -> int:
        return self._CHUNK_SIZE

    @property
    def CHUNKS_PER_SECOND(self) -> int:
        return self._SAMPLING_RATE // self._CHUNK_SIZE

    def _pyaudio_callback(
        self, audio_buffer: bytes | None, frame_count: int, time_info: Mapping[str, float], status: int
    ) -> tuple[bytes | None, int]:
        assert self._callback is not None

        if audio_buffer is None:
            return None, paContinue

        samples = np.frombuffer(audio_buffer, dtype=np.float32)
        self._callback(samples)
        return None, paContinue

    def start(self, callback: AudioSourceCallback) -> None:
        self._callback = callback
        self._stream.start_stream()

    def stop(self) -> None:
        self._stream.stop_stream()
        self._stream.close()
        self._pa.terminate()
