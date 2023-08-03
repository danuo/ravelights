from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array
from ravelights.effects.effect_super import Effect


class EffectColorSwap(Effect):
    def reset(self):
        self.counter = 0

    def on_delete(self):
        ...

    def render_settings_overwrite(self, timeline_level: int) -> dict:
        self.counter += 1
        if self.counter % 1 == 0:
            colors = self.settings.color_engine.get_colors_rgb(timeline_level=timeline_level)
            settings_overwrite = dict(prim_color=colors[1], sec_color=colors[0])
            return settings_overwrite
        else:
            return dict()

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        return in_matrix
