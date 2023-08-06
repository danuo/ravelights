from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ravelights import RaveLightsApp
    from ravelights.interface.artnet.artnet_transmitter import ArtnetTransmitter


@dataclass
class DataLight:
    device: int
    light: int
    flip: bool = False


class DataRouter:
    def __init__(self, root: "RaveLightsApp", transmitter: "ArtnetTransmitter", output_config: list[list[DataLight]]):
        self.root = root
        self.settings = self.root.settings
        self.devices = self.root.devices
        self.output_config = output_config
        self.transmitter = transmitter
        self.output_config = output_config  # need to save this?
        self.process_output_config(output_config)
        # todo: nick
        # self.leds_per_output holds led numbers [720 720 0 0]
        # lights144_per_output holds light numbers [5 5 0 0]
        lights144_per_output = [n // 144 for n in self.leds_per_output]
        self.transmitter.transmit_output_config(lights144_per_output)

        # one out matrix per datarouter / transmitter
        self.out_matrices = np.zeros((self.n, 3), dtype=np.uint8)

    def process_output_config(self, output_config: list[list[DataLight]]):
        self.leds_per_output = []
        self.datalight_objects = []
        for datalights in output_config:
            n = 0
            for datalight in datalights:
                self.datalight_objects.append(datalight)
                n += self.devices[datalight.device].n_leds
            self.leds_per_output.append(n)
        self.n = sum(self.leds_per_output)

    def transmit_matrix(self, int_matrices):
        index = 0
        for d in self.datalight_objects:
            matrix_view = int_matrices[d.device][:, d.light, :]
            length = matrix_view.shape[0]
            # todo: flip
            self.out_matrices[index : index + length] = matrix_view
            index += length

        self.transmitter.transmit_matrix(matrix=self.out_matrices)
