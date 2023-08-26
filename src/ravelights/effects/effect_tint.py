from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array
from ravelights.effects.effect_super import Effect


class EffectTint(Effect):
    def reset(self):
        ...

    def on_delete(self):
        ...

    def run_before(self):
        curent_colors = self.settings.color_engine.get_colors_rgb(timeline_level=0)
        self.settings.color_engine.color_overwrite[0] = curent_colors[2]
        self.settings.color_engine.color_overwrite[1] = curent_colors[2]

    def run_after(self):
        for i in range(2):
            self.settings.color_engine.color_overwrite[i] = None

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        return in_matrix