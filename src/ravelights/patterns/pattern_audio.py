from typing import Literal

from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern

BANDS = Literal["lows", "mids", "highs"]


class PatternAudio(Pattern):
    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, colors: list[Color]) -> ArrayFloat:
        matrix = self.get_float_matrix_2d_mono()

        index_lows = int(self.n_leds * min(1.0, abs(self.audio_data["level_low"])))
        index_mid = int(self.n_leds * min(1.0, abs(self.audio_data["level_mid"])))
        index_high = int(self.n_leds * min(1.0, abs(self.audio_data["level_high"])))

        matrix[:index_lows, 0] = 1.0
        matrix[:index_mid, 1] = 1.0
        matrix[:index_high, 2] = 1.0

        if self.audio_data["is_beat"]:
            matrix[:, 3] = 1.0

        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
