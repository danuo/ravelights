import random

import numpy as np
from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Vfilter


class VfilterMapPropagate(Vfilter):
    def init(self):
        pass

    def alternate(self):
        ...

    def sync_send(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        output_intensity = np.zeros(self.n_lights)
        output_intensity[2] = 1.0
        # todo: fmin

        out_matrix = self.get_float_matrix_rgb()
        for i in range(self.n_lights):
            out_matrix[:, i, :] = output_intensity[i] * in_matrix[:, i, :]
        return out_matrix
