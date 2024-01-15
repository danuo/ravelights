import random

import numpy as np
from ravelights.core.color_handler import Color, ColorHandler
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Generator
from ravelights.effects.effect_super import Effect


class EffectColorStrobeRainbowPixel(Effect):
    def reset(self):
        """
        hue_range controls the color variation for each frame
        """

        self.color_matrix = self.get_color_matrix()

    def run_before(self):
        ...

    def run_after(self):
        ...

    def alternate(self):
        self.color_matrix = self.get_color_matrix()

    def get_color_matrix(self):
        color_matrix = np.zeros((self.n, 3))
        color_matrix[:, 0] = np.random.rand(self.n)
        color_matrix[:, 1] = 1.0
        rng = np.random.default_rng()
        rng.shuffle(color_matrix, axis=-1)  # same shuffle for each row
        color_matrix = color_matrix.reshape((self.n_leds, self.n_lights, 3), order="F")
        return color_matrix

    def render_matrix(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        """Called each render cycle"""
        self.color_matrix = np.roll(self.color_matrix, shift=1, axis=0)

        bw_matrix_mono = Generator.bw_matrix(in_matrix)
        matrix_out = bw_matrix_mono[..., None] * self.color_matrix

        return matrix_out

    def on_delete(self):
        pass


if __name__ == "__main__":
    for _ in range(10):
        random_hue = random.random()
        random_color = ColorHandler.get_color_from_hue(random_hue)
        print(random_color, sum(random_color))
