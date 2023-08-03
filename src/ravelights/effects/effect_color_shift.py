import random

from ravelights.core.colorhandler import Color, ColorHandler
from ravelights.core.custom_typing import Array
from ravelights.effects.effect_super import Effect


class EffectColorShift(Effect):
    def reset(self, hue_range=None):
        """
        starts at the current primary color and ramps from there, then jumps back to the color before

        hue_range in (0,1]
        hue_range controls the color variation for each frame
        """

        self.base_hue = None
        self.sign = random.choice([1, -1])
        self.hue_slide_speed = random.choice([0.05, 0.02, 0.01, 0.005])
        self.hue_slide_speed = 0.01
        print(self.hue_slide_speed)

    def render_settings_overwrite(self, selected_level: int) -> dict[str, Color]:
        if self.base_hue is None:
            curent_color = self.settings.color_engine.get_colors_rgb(selected_level=selected_level)[0]
            current_hue = ColorHandler.get_hue_from_rgb(curent_color)
            self.base_hue = current_hue
            print(self.base_hue)

        new_hue = (self.base_hue + self.sign * self.hue_slide_speed) % 1
        new_color = ColorHandler.get_color_from_hue(new_hue)
        self.base_hue = new_hue

        settings_overwrite = dict(color_prim=new_color)
        return settings_overwrite

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        """Called each render cycle"""
        return in_matrix

    def on_delete(self):
        pass
