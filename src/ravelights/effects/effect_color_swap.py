from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.effects.effect_super import Effect


class EffectColorSwap(Effect):
    def reset(self):
        ...

    def on_delete(self):
        ...

    def run_before(self):
        color_keys = self.settings.color_engine.get_color_keys(timeline_level=1)
        curent_colors = self.settings.color_engine.get_colors_rgb(timeline_level=1)
        self.settings.color_engine.color_overwrite[color_keys[0]] = curent_colors[1]
        self.settings.color_engine.color_overwrite[color_keys[1]] = curent_colors[0]

    def run_after(self):
        self.settings.color_engine.reset_color_overwrite()

    def render_matrix(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        return in_matrix
