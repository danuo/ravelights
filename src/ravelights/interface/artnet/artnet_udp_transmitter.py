import errno
import socket

from loguru import logger
from ravelights.interface.artnet.artnet_transmitter import ArtnetTransmitter


class ArtnetUdpTransmitter(ArtnetTransmitter):
    def __init__(self, ip_address: str | None = None, start_universe: int = 0, debug: bool = False) -> None:
        super().__init__(start_universe=start_universe, debug=False)
        self._PORT = 6454
        self._ip_address = ip_address
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._was_error_logged = False

    def _send_bytes(self, data: bytes) -> None:
        if self._ip_address is not None:
            try:
                self._udp_socket.sendto(data, (self._ip_address, self._PORT))
                if self._was_error_logged:
                    logger.info("Network is reachable again. Artnet transmission re-enabled.")
                    self._was_error_logged = False
            except socket.error as e:
                if e.errno == errno.ENETUNREACH:
                    if not self._was_error_logged:
                        logger.exception("Network is unreachable. Artnet transmission is temporarily disabled.")
                        self._was_error_logged = True
                else:
                    raise

    def update_ip_address(self, ip_address: str | None) -> None:
        self._ip_address = ip_address

        if ip_address is None:
            logger.warning("Artnet transmission disabled until valid IP address is set")
        else:
            logger.info(f"Artnet transmission to {ip_address} enabled")
