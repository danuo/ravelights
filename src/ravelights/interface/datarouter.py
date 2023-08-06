from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ravelights import RaveLightsApp
    from ravelights.interface.artnet.artnet_transmitter import ArtnetTransmitter


@dataclass
class DataLight:
    device: int
    light: int
    flip: bool = False


class DataRouter:
    def __init__(self, root: "RaveLightsApp", transmitter: "ArtnetTransmitter", output_config: list[list[dict]]):
        self.root = root
        self.settings = self.root.settings
        self.devices = self.root.devices
        self.output_config = output_config
        self.transmitter = transmitter
        self.transmitter.transmit_output_config(self.settings.lights_per_output)
        self.output_config = output_config

    def transmit_matrix(self):
        # todo
        matrix = None
        self.transmitter.transmit_matrix(matrix=matrix)
