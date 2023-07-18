import random

from ravelights.core.colorhandler import Color, ColorHandler
from ravelights.core.custom_typing import Array
from ravelights.effects.effect_super import Effect


class EffectColorStrobe(Effect):
    def init(self, hue_range=None):
        # todo: many versions, rainbow, strobe, random, etc pp
        """
        hue_range in (0,1]
        hue_range controls the color variation for each frame
        """

        self.base_hue = random.random()
        self.sign = random.choice([1, -1])
        self.hue_range = hue_range if hue_range else random.choice([1.0, 0.3, 0.1, 0.05])
        self.hue_range = 0.1

    def render_settings_overwrite(self, selected_level: int) -> dict[str, Color]:
        settings_overwrite = dict()
        for key in ["color_prim", "color_sec"]:
            random_hue_shift = random.uniform(0, self.hue_range)
            new_hue = (self.base_hue + self.sign * random_hue_shift) % 1
            random_color = ColorHandler.get_color_from_hue(new_hue)
            settings_overwrite[key] = random_color
        return settings_overwrite

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        """Called each render cycle"""
        return in_matrix

    def on_delete(self):
        pass
