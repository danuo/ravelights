import random

from ravelights.core.colorhandler import Color, ColorHandler
from ravelights.core.custom_typing import Array
from ravelights.core.generator_super import Generator
from ravelights.effects.effect_super import Effect
from ravelights.vfilters.vfilter_bw import VfilterBW


class EffectColorStrobeRainbow(Effect):
    def reset(self):
        """
        hue_range controls the color variation for each frame
        """

        self.bw_filter = VfilterBW(root=self.root, device=self.device)

    def render_settings_overwrite(self, selected_level: int) -> dict[str, Color]:
        return dict()

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        """Called each render cycle"""
        bw_matrix_mono = Generator.bw_matrix(in_matrix)

        matrix_out = self.bw_filter.get_float_matrix_rgb()

        for light_id in range(self.n_lights):
            matrix_view = bw_matrix_mono[:, light_id]
            random_hue = random.random()
            random_color = ColorHandler.get_color_from_hue(random_hue)
            colored_matrix = self.bw_filter.colorize_matrix(matrix_mono=matrix_view, color=random_color)
            matrix_out[:, light_id, :] = colored_matrix

        return matrix_out

    def on_delete(self):
        pass
