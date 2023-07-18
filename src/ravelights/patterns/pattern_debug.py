from itertools import product

import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.generator_super import Pattern


class PatternDebug(Pattern):
    def init(self):
        variants = list(product([True, False], repeat=3))
        gradient = np.linspace(0.0, 1.0, self.n_leds)
        matrix = self.get_float_matrix_rgb()
        for light_id in range(self.n_lights):
            var = variants[light_id]
            for channel_id in range(3):
                if var[channel_id]:
                    matrix[:, light_id, channel_id] = gradient
        self.matrix = matrix

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, color: Color):
        return self.matrix
