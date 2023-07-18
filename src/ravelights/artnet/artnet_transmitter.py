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
        self._start_universe = start_universe
        self._debug = debug

    def transmit_matrix(self, matrix: npt.NDArray[np.uint8]) -> None:
        """Transmit the pixel data in the provided matrix to the receiving Artnet node

        Args:
            matrix (np.typing.NDArray): An Nx3 ndarray containing r,g,b values for each of the N to
            be addressed pixels. Each color value must be an integer in {0, ..., 255}
            (dtype=np.uint8), e.g. matrix[0] = [255, 0, 0] sets the first pix>el to red.
        """
        assert matrix.dtype == np.uint8
        assert matrix.ndim == 3
        assert matrix.shape[2] == 3

        matrix_2d = matrix.reshape((-1, 3), order="F")
        channels = matrix.flatten()
        self._transmit_channels(channels)

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
