import random

import numpy as np
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array
from ravelights.core.generator_super import Thinner
from ravelights.core.timehandler import BeatStatePattern


class ThinnerRandom(Thinner):
    def init(self):
        self.possible_triggers = [
            BeatStatePattern(beats=[0], quarters="ABCD", loop_length=1),
            BeatStatePattern(beats=[0], quarters="A", loop_length=1),
            BeatStatePattern(beats=[0], quarters="A", loop_length=4),
            BeatStatePattern(beats=[0, 1], quarters="A", loop_length=4),
            BeatStatePattern(beats=[0, 2], quarters="A", loop_length=4),
        ]
        self.mask = self.get_float_matrix_1d_mono(fill_value=1)

    def alternate(self):
        self.trigger = random.choice(self.possible_triggers)

    def reset(self):
        self.on_trigger()

    def on_trigger(self):
        self.mask[:] = 1
        if self.settings.global_thinning_ratio >= 1.0:
            return
        shape = self.mask.shape
        random = np.random.random(size=shape)
        self.mask = np.where(random < self.settings.global_thinning_ratio, 1, 0)

    def render(self, in_matrix: Array, colors: list[Color]):
        matrix = self.apply_mask(in_matrix=in_matrix, mask=self.mask.reshape(self.n_leds, -1))
        return matrix
