import queue
import threading

import serial
from loguru import logger  # type:ignore
from ravelights.interface.artnet.artnet_transmitter import ArtnetTransmitter


class ArtnetSerialTransmitter(ArtnetTransmitter):
    def __init__(
        self,
        serial_port_address: str = "/dev/ttyAMA0",
        baud_rate: int = 3_000_000,
        start_universe: int = 0,
        debug: bool = False,
    ):
        super().__init__(start_universe=start_universe, debug=debug)
        self._serial_port = serial.Serial(port=serial_port_address, baudrate=baud_rate)
        self._output_queue: queue.Queue[bytes] = queue.Queue()

        threading.Thread(target=self._send_thread, daemon=True).start()

    def _send_bytes(self, data: bytes) -> None:
        self._output_queue.put(data)

    def _send_thread(self):
        while True:
            data = self._output_queue.get()
            self._serial_port.write(data)
