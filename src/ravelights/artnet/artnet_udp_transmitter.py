import socket

from ravelights.artnet.artnet_transmitter import ArtnetTransmitter


class ArtnetUdpTransmitter(ArtnetTransmitter):
    def __init__(self, ip_address: str, start_universe: int = 0, debug: bool = False) -> None:
        super().__init__(start_universe=start_universe, debug=debug)
        self._PORT = 6454
        self._ip_address = ip_address
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _send_bytes(self, data: bytes) -> None:
        self._udp_socket.sendto(data, (self._ip_address, self._PORT))
