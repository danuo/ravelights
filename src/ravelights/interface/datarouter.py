from typing import TYPE_CHECKING

import numpy as np
from ravelights.core.custom_typing import ArrayUInt8, TransmitDict

if TYPE_CHECKING:
    from ravelights import RaveLightsApp
    from ravelights.interface.artnet.artnet_transmitter import ArtnetTransmitter


class DataRouter:
    def __init__(
        self, root: "RaveLightsApp", transmitter: "ArtnetTransmitter", transmitter_config: list[list[TransmitDict]]
    ):
        self.root = root
        self.settings = self.root.settings
        self.devices = self.root.devices
        self.transmitter = transmitter
        self.leds_per_output, self.out_lights, self.n = self.process_transmitter_config(transmitter_config)
        self.transmitter.transmit_output_config(self.leds_per_output)
        # one out matrix per datarouter / transmitter
        self.out_matrix = np.zeros((self.n, 3), dtype=np.uint8)

    def process_transmitter_config(self, output_config: list[list[TransmitDict]]):
        leds_per_output: list[int] = []
        out_lights: list[TransmitDict] = []
        for conf in output_config:
            n: int = 0
            for out_light in conf:
                out_lights.append(out_light)
                n += self.devices[out_light["device"]].n_leds
            leds_per_output.append(n)
        n = self.leds_per_output
        return leds_per_output, out_lights, n

    def transmit_matrix(self, out_matrices_int: list[ArrayUInt8]):
        index = 0
        for out_light in self.out_lights:
            matrix_view = out_matrices_int[out_light["device"]][:, out_light["light"], :]
            length = matrix_view.shape[0]
            if "flip" in out_light and out_light["flip"]:
                matrix_view = np.flip(matrix_view, axis=0)
            self.out_matrix[index : index + length] = matrix_view
            index += length

        self.transmitter.transmit_matrix(matrix=self.out_matrix)
