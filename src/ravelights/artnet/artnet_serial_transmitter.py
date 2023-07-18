import serial

from ravelights.artnet.artnet_transmitter import ArtnetTransmitter


class ArtnetSerialTransmitter(ArtnetTransmitter):
    def __init__(
        self,
        serial_port_address: str = "/dev/ttyAMA0",
        baud_rate: int = 460800,
        start_universe: int = 0,
        debug: bool = False,
    ):
        super().__init__(start_universe=start_universe, debug=debug)
        self._serial_port = serial.Serial(port=serial_port_address, baudrate=baud_rate)

    def _send_bytes(self, data: bytes) -> None:
        self._serial_port.write(data)
