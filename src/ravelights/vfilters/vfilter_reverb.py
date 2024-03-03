import random

import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Vfilter


class VfilterReverb(Vfilter):
    def init(self):
        self.out_matrix = self.get_float_matrix_rgb()
        self.decay = 0.7
        self.version = 2
        if self.version == 0:
            self.version = random.choice([1, 2])
        elif self.version == 1:
            self.decay = 0.7
        elif self.version == 2:
            self.decay = 0.85

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: tuple[Color, Color]) -> ArrayFloat:
        self.out_matrix *= self.decay
        self.out_matrix += in_matrix

        # normalization method 1
        # max_intensity = np.max(self.out_matrix)
        # if max_intensity > 1.0:
        # self.out_matrix /= max_intensity

        # normalization method 2
        if np.max(self.out_matrix) > 1.0:
            max_bright = np.fmax(np.max(self.out_matrix, axis=-1), 1)
            self.out_matrix /= max_bright[..., None]
        return self.out_matrix
