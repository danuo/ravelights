import random

import numpy as np
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Vfilter


class VfilterRgbShift(Vfilter):
    def init(self):
        self.limit = 30
        self.order = [0, 1, 2]
        self.mode = 0

    def alternate(self):
        if self.mode == 0:
            self.mode = random.choice([1, 2])
        if self.mode == 1:
            self.init_shift = 0
            self.shift_speed = 1
        if self.mode == 2:
            self.init_shift = 5
            self.shift_speed = 0
        self.shift = self.init_shift

    def reset(self):
        ...

    def on_trigger(self):
        self.shift = self.init_shift
        random.shuffle(self.order)

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        if self.timehandler.beat_state.is_beat:
            self.on_trigger()
        if self.shift > self.limit:
            return in_matrix
        self.shift += self.shift_speed
        rolls = [0, self.shift, -self.shift]
        in_matrix_bw = self.bw_matrix(in_matrix)
        out_matrix_rgb = np.concatenate(
            [
                np.roll(in_matrix_bw, shift=rolls[self.order[0]], axis=0)[..., None],
                np.roll(in_matrix_bw, shift=rolls[self.order[1]], axis=0)[..., None],
                np.roll(in_matrix_bw, shift=rolls[self.order[2]], axis=0)[..., None],
            ],
            axis=-1,
        )
        return out_matrix_rgb
