import serial
import logging

from ravelights.artnet.artnet_transmitter import ArtnetTransmitter

logger = logging.getLogger(__name__)


class ArtnetSerialTransmitter(ArtnetTransmitter):
    def __init__(
        self,
        serial_port_address: str = "/dev/ttyAMA0",
        baud_rate: int = 3_000_000,
        start_universe: int = 0,
        debug: bool = False,
    ):
        super().__init__(start_universe=start_universe, debug=debug)
        self._serial_port = serial.Serial(port=serial_port_address, baudrate=baud_rate, write_timeout=0)

    def _send_bytes(self, data: bytes) -> None:
        if not self._serial_port.writable():
            logger.warn("Serial port not ready for writing yet. Skipping this frame...")
            return

        self._serial_port.write(data)
