from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
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

    def render(self, in_matrix: ArrayFloat, colors: tuple[Color, Color]) -> ArrayFloat:
        assert in_matrix.shape == (self.n_leds, self.n_lights, 3), in_matrix.shape
        n = self.n_lights // 2
        for i in range(n):
            in_matrix[:, i, :] = in_matrix[:, -i - 1, :]
        return in_matrix
