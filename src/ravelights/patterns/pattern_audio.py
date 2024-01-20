from typing import Literal

import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern

BAND: list[Literal[str]] = ["lows", "mids", "highs"]


class PatternAudio(Pattern):
    DECAY = 0.8

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, colors: list[Color]) -> ArrayFloat:
        matrix = self.get_float_matrix_1d_mono()
        for light_id in range(self.n_lights):
            pass

        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
