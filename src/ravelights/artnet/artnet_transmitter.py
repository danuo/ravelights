import numpy as np
import numpy.typing as npt
from abc import ABCMeta, abstractmethod

from ravelights.artnet.art_dmx_packet import ArtDmxPacket


class ArtnetTransmitter(metaclass=ABCMeta):
    def __init__(
        self,
        start_universe: int = 0,
        debug: bool = False,
    ):
        self._UNIVERSE_SIZE = 512
        self._CONFIG_UNIVERSE_INDEX = 0xFF
        self._start_universe = start_universe
        self._debug = debug

    def transmit_matrix(self, matrix: npt.NDArray[np.uint8]) -> None:
        """Transmit the pixel data in the provided matrix to the receiving Artnet node

        Args:
            matrix (np.typing.NDArray): An MxNx3 ndarray containing r,g,b values for each of the M * N to
            be addressed pixels. Each color value must be an integer in {0, ..., 255}
            (dtype=np.uint8), e.g. matrix[0, 0] = [255, 0, 0] sets the first pixel to red.
        """
        assert matrix.dtype == np.uint8
        assert matrix.ndim == 3
        assert matrix.shape[2] == 3

        # Reshape 3D matrix into 1D array corresponding to the Art-Net DMX data format
        channels = matrix.reshape((-1, 3), order="F").flatten()

        self._transmit_channels(channels)

    def transmit_output_config(self, lights_per_output: list[int]) -> None:
        assert len(lights_per_output) == 4

        checksum = sum(lights_per_output)
        channels = np.array([*lights_per_output, checksum], dtype=np.uint8)
        self._send_universe(universe=self._CONFIG_UNIVERSE_INDEX, data=channels)

    def _transmit_channels(self, channels: npt.NDArray[np.uint8]):
        for i, universe_data in enumerate(self._split_universes(channels), start=self._start_universe):
            self._send_universe(i, universe_data)

    def _split_universes(self, channels: npt.NDArray[np.uint8]) -> list[npt.NDArray[np.uint8]]:
        return [channels[i : i + self._UNIVERSE_SIZE] for i in range(0, len(channels), self._UNIVERSE_SIZE)]

    def _send_universe(self, universe: int, data: npt.NDArray[np.uint8]):
        data_bytes = data.tobytes()
        artnet_packet = ArtDmxPacket(universe=universe, data=data_bytes, length=len(data_bytes))

        if self._debug:
            artnet_packet.output_data()

        self._send_bytes(data=artnet_packet.get_bytes())

    @abstractmethod
    def _send_bytes(self, data: bytes) -> None:
        pass
