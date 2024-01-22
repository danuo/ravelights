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

        indices_max: list[int] = []
        channels: list[slice | int] = []
        intensities: list[float] = []

        index_cap = self.n_leds - 1

        index_is_beat = index_cap if self.audio_data["is_beat"] else 0
        indices_max.append(index_is_beat)
        channels.append(slice(None, None, None))  # white
        intensities.append(1.0)  # full

        index_rms = int(index_cap * min(1.0, abs(self.audio_data["rms"])))
        indices_max.append(index_rms)
        channels.append(slice(None, None, None))  # white
        intensities.append(0.5)  # half

        index_level_total = int(index_cap * self.audio_data["level"])
        indices_max.append(index_level_total)
        channels.append(0)  # red
        intensities.append(1.0)  # full

        index_presence_total = int(index_cap * self.audio_data["presence"])
        indices_max.append(index_presence_total)
        channels.append(0)  # red
        intensities.append(0.5)  # half

        index_level_lows = int(index_cap * self.audio_data["level_low"])
        indices_max.append(index_level_lows)
        channels.append(1)  # green
        intensities.append(1.0)  # full

        index_presence_lows = int(index_cap * self.audio_data["presence_low"])
        indices_max.append(index_presence_lows)
        channels.append(1)  # green
        intensities.append(0.5)  # half

        index_level_mids = int(index_cap * self.audio_data["level_mid"])
        indices_max.append(index_level_mids)
        channels.append(2)  # blue
        intensities.append(1.0)  # gray

        index_presence_mids = int(index_cap * self.audio_data["presence_mid"])
        indices_max.append(index_presence_mids)
        channels.append(2)  # blue
        intensities.append(0.5)  # gray

        index_level_highs = int(index_cap * self.audio_data["level_high"])
        indices_max.append(index_level_highs)
        channels.append(slice(-1, 1))  # purple
        intensities.append(1.0)  # gray

        index_presence_highs = int(index_cap * self.audio_data["presence_high"])
        indices_max.append(index_presence_highs)
        channels.append(slice(-1, 1))  # purple
        intensities.append(0.5)  # half

        for light_id in range(self.n_lights):
            matrix_rgb[: indices_max[light_id], light_id, channels[light_id]] = intensities[light_id]

        return matrix_rgb
