import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayMxKx3
from ravelights.core.generator_super import Vfilter


class VfilterRollOverlay(Vfilter):
    def init(self):
        self.roll_speed = 1

    def alternate(self):
        ...

    def reset(self):
        self.roll_amount = 0

    def on_trigger(self):
        self.roll_amount = 0

    def render(self, in_matrix: ArrayMxKx3, colors: list[Color]) -> ArrayMxKx3:
        self.roll_amount += self.roll_speed
        out_matrix = in_matrix.copy()
        out_matrix += np.roll(in_matrix, shift=self.roll_amount, axis=0)
        out_matrix += np.roll(in_matrix, shift=-self.roll_amount, axis=0)

        # normalization
        if np.max(out_matrix) > 1.0:
            max_bright = np.fmax(np.max(out_matrix, axis=-1), 1)
            out_matrix /= max_bright[..., None]
        return out_matrix
