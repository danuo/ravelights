import random

import numpy as np

from ravelights.core.colorhandler import Color, ColorHandler
from ravelights.core.custom_typing import ArrayMxKx3
from ravelights.core.generator_super import Generator
from ravelights.effects.effect_super import Effect
from ravelights.vfilters.vfilter_bw import VfilterBW


class EffectColorStrobeRainbowPixel(Effect):
    def reset(self):
        """
        hue_range controls the color variation for each frame
        """

        self.bw_filter = VfilterBW(root=self.root, device=self.device)
        self.randi = None

    def render_settings_overwrite(self, selected_level: int) -> dict[str, Color]:
        return dict()

    def render_matrix(self, in_matrix: ArrayMxKx3, color: Color) -> ArrayMxKx3:
        """Called each render cycle"""
        if self.randi is None:
            color_matrix = np.zeros((self.n, 3))
            color_matrix[:, 0] = np.random.rand(self.n)
            color_matrix[:, 1] = 1.0
            rng = np.random.default_rng()
            rng.shuffle(color_matrix, axis=-1)  # same shuffle for each row
            color_matrix = color_matrix.reshape((self.n_leds, self.n_lights, 3), order="F")
            self.randi = color_matrix
        else:
            self.randi = np.roll(self.randi, shift=1, axis=0)

        bw_matrix_mono = Generator.bw_matrix(in_matrix)
        matrix_out = bw_matrix_mono[..., None] * self.randi

        return matrix_out

    def on_delete(self):
        pass


if __name__ == "__main__":
    for _ in range(10):
        random_hue = random.random()
        random_color = ColorHandler.get_color_from_hue(random_hue)
        print(random_color, sum(random_color))
