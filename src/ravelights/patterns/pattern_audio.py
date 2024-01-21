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

        assert 0 <= self.audio_data["level_low"] <= 1.0
        assert 0 <= self.audio_data["level_mid"] <= 1.0
        assert 0 <= self.audio_data["level_high"] <= 1.0
        assert 0 <= self.audio_data["level"] <= 1.0

        assert 0 <= self.audio_data["presence_low"] <= 1.0
        assert 0 <= self.audio_data["presence_mid"] <= 1.0
        assert 0 <= self.audio_data["presence_high"] <= 1.0
        assert 0 <= self.audio_data["presence"] <= 1.0

        index_rms = int(self.n_leds * min(1.0, abs(self.audio_data["rms"])))
        index_level_lows = int(self.n_leds * self.audio_data["level_low"])
        index_level_mids = int(self.n_leds * self.audio_data["level_mid"])
        index_level_highs = int(self.n_leds * self.audio_data["level_high"])
        index_level_total = int(self.n_leds * self.audio_data["level"])

        index_presence_lows = int(self.n_leds * self.audio_data["presence_low"])
        index_presence_mids = int(self.n_leds * self.audio_data["presence_mid"])
        index_presence_highs = int(self.n_leds * self.audio_data["presence_high"])
        index_presence_total = int(self.n_leds * self.audio_data["presence"])

        for light_id in range(self.n_lights):
            match light_id:  # match statement to support devices with few n_lights in tests
                case 0:
                    if self.audio_data["is_beat"]:
                        matrix_rgb[:, 0, :] = 1.0  # white
                case 1:
                    matrix_rgb[:index_rms, 1, :] = 0.5  # gray
                case 2:
                    matrix_rgb[:index_level_total, 2, 0] = 1.0  # red
                case 3:
                    matrix_rgb[:index_presence_total, 3, 0] = 0.5  # dark red
                case 4:
                    matrix_rgb[:index_level_lows, 4, 1] = 1.0  # green
                case 5:
                    matrix_rgb[:index_presence_lows, 5, 1] = 0.5  # dark green
                case 6:
                    matrix_rgb[:index_level_mids, 6, 2] = 1.0  # blue
                case 7:
                    matrix_rgb[:index_presence_mids, 7, 2] = 0.5  # dark blue
                case 8:
                    matrix_rgb[:index_level_highs, 8] = [1.0, 0, 1.0]  # purple
                case 9:
                    matrix_rgb[:index_presence_highs, 9] = [0.5, 0, 0.5]  # dark purple

        return matrix_rgb
