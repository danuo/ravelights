import random

import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat, LightSequence
from ravelights.core.generator_super import Vfilter
from ravelights.core.time_handler import BeatStatePattern
from ravelights.core.utils import LightSequenceGenerator


class Propagation:
    def __init__(self, n_lights: int, light_sequence: LightSequence) -> None:
        self.n_lights = n_lights
        self.light_sequence: LightSequence = light_sequence
        self.frame_counter: int = 0

    def get_output_intensity(self) -> ArrayFloat:
        """Returns an array of light intensities. Contains one value for each light"""

        out_intensity = np.zeros(self.n_lights)
        light_indices = self.light_sequence[self.frame_counter]
        for light_index in light_indices:
            out_intensity[light_index] = 1.0
        self.frame_counter += 1
        return out_intensity

    def done(self) -> bool:
        if self.frame_counter >= len(self.light_sequence):
            return True
        else:
            return False


class VfilterMapPropagate(Vfilter):
    def init(self) -> None:
        if self.version == 0:
            self.mode = random.choice([0, 1, 2, 3])
        elif self.version == 1:
            self.mode = 0
        elif self.version == 2:
            self.mode = 1
        elif self.version == 3:
            self.mode = 2
        elif self.version == 4:
            self.mode = 3

        self.possible_triggers = [
            BeatStatePattern(loop_length=1),
        ]
        self.props: list[Propagation] = []

    def alternate(self):
        ...

    def sync_send(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):  #
        if self.mode == 0:
            light_sequence = LightSequenceGenerator.left_to_right(self.n_lights)
        elif self.mode == 1:
            light_sequence = LightSequenceGenerator.left_to_right(self.n_lights, reverse=True)
        if self.mode == 2:
            light_sequence = LightSequenceGenerator.out_to_mid(self.n_lights)
        elif self.mode == 3:
            light_sequence = LightSequenceGenerator.out_to_mid(self.n_lights, reverse=True)

        self.props.append(Propagation(self.n_lights, light_sequence))

    def render(self, in_matrix: ArrayFloat, colors: tuple[Color, Color]) -> ArrayFloat:
        total_out_intensity = np.zeros(self.n_lights)

        for prop in self.props:
            out_intensity = prop.get_output_intensity()
            total_out_intensity += out_intensity
            if prop.done():
                self.props.remove(prop)

        total_out_intensity = np.fmin(1.0, total_out_intensity)

        out_matrix = self.get_float_matrix_rgb()
        for i in range(self.n_lights):
            out_matrix[:, i, :] = total_out_intensity[i] * in_matrix[:, 0, :]
        return out_matrix
