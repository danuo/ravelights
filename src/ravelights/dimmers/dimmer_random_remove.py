import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array
from ravelights.core.generator_super import Dimmer
from ravelights.core.utils import p


class DimmerRandomRemove(Dimmer):
    def init(self):
        self.mask = self.get_float_matrix_1d_mono(fill_value=1.0)

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        self.mask[:] = 1.0

    def step(self):
        # progress thinning mask
        for i in np.nonzero(self.mask)[0]:
            if p(0.1):
                self.mask[i] = False

    def render(self, in_matrix: Array, color: Color) -> Array:
        self.step()  # todo: set this to seperate trigger
        matrix = self.apply_mask(in_matrix=in_matrix, mask=self.mask.reshape(self.n_leds, -1))
        return matrix
