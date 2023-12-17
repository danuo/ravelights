import logging
import socket

from ravelights.interface.artnet.artnet_transmitter import ArtnetTransmitter

logger = logging.getLogger(__name__)


class ArtnetUdpTransmitter(ArtnetTransmitter):
    def __init__(self, ip_address: str | None = None, start_universe: int = 0, debug: bool = False) -> None:
        super().__init__(start_universe=start_universe, debug=False)
        self._PORT = 6454
        self._ip_address = ip_address
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _send_bytes(self, data: bytes) -> None:
        if self._ip_address is not None:
            self._udp_socket.sendto(data, (self._ip_address, self._PORT))

    def update_ip_address(self, ip_address: str | None) -> None:
        self._ip_address = ip_address

        if ip_address is None:
            logger.warn("Artnet transmission disabled until valid IP address is set")
        else:
            logger.info(f"Artnet transmission to {ip_address} enabled")
