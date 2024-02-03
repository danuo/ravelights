from typing import Callable, Mapping, Optional

import numpy as np
from loguru import logger
from numpy.typing import NDArray
from pyaudio import PyAudio, paContinue, paFloat32

AudioSourceCallback = Callable[[NDArray[np.float32]], None]


class AudioSource:
    def __init__(
        self,
        sampling_rate: int = 44100,
        chunk_size: int = 512,
        input_device_index: Optional[int] = None,
    ) -> None:
        self._SAMPLING_RATE = sampling_rate
        self._CHUNK_SIZE = chunk_size

        self._pa = PyAudio()

        self.list_all_audio_devices()
        self.list_default_audio_device()

        self._stream = self._pa.open(
            format=paFloat32,
            channels=1,
            rate=sampling_rate,
            input=True,
            frames_per_buffer=chunk_size,
            stream_callback=self._pyaudio_callback,
            input_device_index=input_device_index,
            start=False,
        )
        self._callback: Optional[AudioSourceCallback] = None

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
        self, audio_buffer: Optional[bytes], frame_count: int, time_info: Mapping[str, float], status: int
    ) -> tuple[Optional[bytes], int]:
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

    def list_all_audio_devices(self):
        message = "listing all audio devices:\n"
        for i in range(self._pa.get_device_count()):
            device_info = self._pa.get_device_info_by_index(i)
            message += f"index: {device_info['index']}, name: {device_info['name']}\n"
        logger.debug(message)

    def list_default_audio_device(self):
        default_input_device_index = self._pa.get_default_input_device_info()["index"]
        device_info = self._pa.get_device_info_by_index(default_input_device_index)

        logger.debug(f"Default Input Device Info: {device_info}")
        logger.info(f"Default Input Device Index: {default_input_device_index}")
        logger.info(f"Default Input Device Name: {device_info['name']}")
