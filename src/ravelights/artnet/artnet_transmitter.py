import socket

import numpy as np
import numpy.typing as npt

from ravelights.artnet.art_dmx_packet import ArtDmxPacket


class ArtnetTransmitter:
    def __init__(self, ip_address: str, start_universe: int = 0, debug: bool = False):
        self._PORT = 6454
        self._UNIVERSE_SIZE = 512
        self._ip_address = ip_address
        self._start_universe = start_universe
        self._debug = debug
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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
        artnet_packet_new = ArtDmxPacket(universe=universe, data=data_bytes, length=len(data_bytes))
        if self._debug:
            artnet_packet_new.output_data()
        self._udp_socket.sendto(artnet_packet_new.get_bytes(), (self._ip_address, self._PORT))
