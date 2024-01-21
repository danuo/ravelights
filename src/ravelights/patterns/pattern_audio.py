from typing import Literal

from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern

BANDS = Literal["lows", "mids", "highs"]


class PatternAudio(Pattern):
    """pattern name: p_audio"""

    def init(self):
        self.p_add_dimmer = 0.0
        self.p_add_thinner = 0.0

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, colors: list[Color]) -> ArrayFloat:
        matrix_rgb = self.get_float_matrix_rgb()

        index_rms = int(self.n_leds * min(1.0, abs(self.audio_data["rms"])))
        index_lows = int(self.n_leds * min(1.0, abs(self.audio_data["level_low"])))
        index_mid = int(self.n_leds * min(1.0, abs(self.audio_data["level_mid"])))
        index_high = int(self.n_leds * min(1.0, abs(self.audio_data["level_high"])))

        for light_id in range(self.n_lights):
            match light_id:  # match statement to support devices with few n_lights in tests
                case 0:
                    if self.audio_data["is_beat"]:
                        matrix_rgb[:, 0, :] = 1.0  # white
                case 1:
                    matrix_rgb[:index_rms, 1, :] = 1.0  # white
                case 2:
                    matrix_rgb[:index_lows, 2, 0] = 1.0  # red
                case 3:
                    matrix_rgb[:index_mid, 3, 1] = 1.0  # green
                case 4:
                    matrix_rgb[:index_high, 4, 2] = 1.0  # blue

        return matrix_rgb
