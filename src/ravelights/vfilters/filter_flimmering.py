import math
import random

from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import Array
from ravelights.core.generator_super import Vfilter
from ravelights.core.utils import p


class VfilterFlimmering(Vfilter):
    def init(self):
        self.counter_frame = random.randint(0, 100)

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    @property
    def sin_factor(self):
        """defines flickering frequency through sin function"""
        if self.settings.global_energy <= 0.5:
            x = (0.05 + self.settings.global_energy) ** 2 * 6  # formerly 2
        else:
            x = 2
        return x

    def render(self, in_matrix: Array, colors: list[Color]) -> Array:
        self.counter_frame = (self.counter_frame + 1) % 1024
        intens: float = abs(math.sin(self.counter_frame * self.sin_factor)) + 0.1
        intens = min(intens, 1)
        if self.settings.global_energy > 0.5:
            if p(self.settings.global_energy * 0.5):
                intens = (intens * 0.7) ** 2
        matrix = in_matrix * intens
        return matrix
