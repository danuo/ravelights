from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ravelights import RaveLightsApp
    from ravelights.interface.artnet.artnet_transmitter import ArtnetTransmitter


class DataRouter:
    def __init__(self, root: "RaveLightsApp", transmitter: "ArtnetTransmitter", output_config: list[list[dict]]):
        self.root = root
        self.settings = self.root.settings
        self.devices = self.root.devices
        self.transmitter = transmitter
        self.process_output_config(output_config)
        # todo: nick
        # self.leds_per_output holds led numbers [720 720 0 0]
        # lights144_per_output holds light numbers [5 5 0 0]
        lights144_per_output = [n // 144 for n in self.leds_per_output]
        self.transmitter.transmit_output_config(lights144_per_output)

        # one out matrix per datarouter / transmitter
        self.out_matrix = np.zeros((self.n, 3), dtype=np.uint8)

    def process_output_config(self, output_config: list[list[dict]]):
        self.leds_per_output = []
        self.out_lights = []
        for out_lights in output_config:
            n = 0
            for out_light in out_lights:
                self.out_lights.append(out_light)
                n += self.devices[out_light["device"]].n_leds
            self.leds_per_output.append(n)
        self.n = sum(self.leds_per_output)

    def transmit_matrix(self, out_matrices_int):
        index = 0
        for d in self.out_lights:
            matrix_view = out_matrices_int[d["device"]][:, d["light"], :]
            length = matrix_view.shape[0]
            if "flip" in d and d["flip"]:
                matrix_view = np.flip(matrix_view, axis=0)
            self.out_matrix[index : index + length] = matrix_view
            index += length

        self.transmitter.transmit_matrix(matrix=self.out_matrix)
