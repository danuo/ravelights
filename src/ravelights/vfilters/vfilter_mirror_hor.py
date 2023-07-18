from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayMxKx3
from ravelights.core.generator_super import Vfilter


class VfilterMirrorHor(Vfilter):
    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayMxKx3, color: Color) -> ArrayMxKx3:
        assert in_matrix.shape == (self.n_leds, self.n_lights, 3)
        n = self.n_lights // 2
        for i in range(n):
            in_matrix[:, i, :] = in_matrix[:, -i - 1, :]
        return in_matrix
