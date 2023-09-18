import random

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat, assert_dims
from ravelights.core.generator_super import Vfilter


class VfilterSomeFirst(Vfilter):
    # todo: possible triggers
    def init(self):
        self.on_trigger()

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        if self.n_lights > 1:
            n_selection = random.choice(range(self.n_lights - 1))
            self.light_ids = random.choices(range(1, self.n_lights), k=n_selection)
        else:
            self.light_ids = [0]

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        assert_dims(in_matrix, self.n_leds, self.n_lights, 3)
        out_matrix = self.get_float_matrix_rgb()
        for i in self.light_ids:
            out_matrix[:, i, :] = in_matrix[:, 0, :]
        return out_matrix
