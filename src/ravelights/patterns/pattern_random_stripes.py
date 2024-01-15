import random

from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern
from ravelights.core.utils import p


class PatternRandomStripes(Pattern):
    """pattern name: p_random_stripes"""

    def init(self):
        self.p_add_dimmer = 0.5

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, colors: list[Color]) -> ArrayFloat:
        matrix = self.get_float_matrix_1d_mono()
        intensity = random.uniform(0, 1)
        for i in range(self.n_lights * self.n_leds):
            if p(0.05):
                intensity = random.uniform(0, 1)
            matrix[i] = intensity
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
