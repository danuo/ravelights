import random

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayMxKx3
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
        n_selection = random.choice(range(self.n_lights - 1))
        self.light_ids = random.choices(range(1, self.n_lights), k=n_selection)
        print("selected lights: ", self.light_ids)

    def render(self, in_matrix: ArrayMxKx3, color: Color) -> ArrayMxKx3:
        assert in_matrix.shape == (self.n_leds, self.n_lights, 3)

        out_matrix = self.get_float_matrix_rgb()
        for i in self.light_ids:
            out_matrix[:, i, :] = in_matrix[:, 0, :]
        return out_matrix