import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Dimmer
from ravelights.core.utils import p


class DimmerRandomRemove(Dimmer):
    def init(self):
        self.mask = self.get_float_matrix_1d_mono(fill_value=1.0)

    def alternate(self):
        ...

    def reset(self):
        self.mask[:] = 1.0
        self.intensity = 0.2
        self.counter_frames = 0

    def on_trigger(self):
        self.reset()

    def step(self):
        if self.counter_frames == 1:
            self.intensity = 0.6
        if self.counter_frames == 2:
            self.intensity = 1.0

        # progress thinning mask
        for i in np.nonzero(self.mask)[0]:
            if p(0.1):
                self.mask[i] = False
        self.counter_frames += 1

    def render(self, in_matrix: ArrayFloat, colors: list[Color]):
        self.step()  # todo: set this to seperate trigger
        matrix = self.apply_mask(in_matrix=self.intensity * in_matrix, mask=self.mask.reshape(self.n_leds, -1))
        return matrix
