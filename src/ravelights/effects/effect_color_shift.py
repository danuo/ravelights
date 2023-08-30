import random
from typing import Optional

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

        self.base_hue: list[Optional[float]] = [None] * 2
        self.sign = random.choice([1, -1])
        self.hue_slide_speed = random.choice([0.05, 0.02, 0.01, 0.005])
        self.hue_slide_speed = 0.01  # todo

    def run_before(self):
        for index, base_hue in enumerate(self.base_hue):
            if base_hue is None:
                curent_color = self.settings.color_engine.get_colors_rgb(timeline_level=1)[index]
                current_hue = ColorHandler.get_hue_from_rgb(curent_color)
                base_hue = current_hue

            new_hue = (base_hue + self.sign * self.hue_slide_speed) % 1
            self.base_hue[index] = new_hue
            new_color = ColorHandler.get_color_from_hue(new_hue)
            self.settings.color_engine.color_overwrite[index] = new_color

    def run_after(self):
        for index in range(2):
            self.settings.color_engine.color_overwrite[index] = None

    def render_matrix(self, in_matrix: Array, colors: list[Color]) -> Array:
        """Called each render cycle"""
        return in_matrix

    def on_delete(self):
        pass
