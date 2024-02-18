import random

import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Generator
from ravelights.effects.effect_super import Effect


class EffectColorize(Effect):
    def reset(self):
        """
        hue_range controls the color variation for each frame
        """

        def get_color_matrix(k: float):
            """generates random matrix with 0 and 1 to colorize in_matrix"""
            color_matrix = np.zeros(shape=(self.n_leds * self.n_lights), dtype=int)
            index = 0
            while index < self.n:
                index += int(abs(random.gauss(mu=50, sigma=30)))
                dist = int(abs(random.gauss(mu=k * 20, sigma=k * 15)))
                color_matrix[index : index + dist] = 1
                index += dist
            return color_matrix.reshape((self.n_leds, self.n_lights), order="F")

        self.color_matrices = [get_color_matrix(k) for k in [0.1, 0.2, 1]]

        self.roll = 0

    def run_before(self):
        ...

    def run_after(self):
        ...

    def render_matrix(self, in_matrix: ArrayFloat, colors: tuple[Color, Color]) -> ArrayFloat:
        # bw filter
        in_matrix_bw = np.max(in_matrix, axis=-1)

        in_matrix_color1 = Generator.colorize_matrix(in_matrix_bw, color=colors[0])
        in_matrix_color2 = Generator.colorize_matrix(in_matrix_bw, color=colors[1])
        self.roll += 1

        # get index
        beat_state = self.timehandler.beat_state
        n_beats = beat_state.n_beats % 2
        quarter = beat_state.string_quarters

        # use index
        if n_beats == 0:
            index = 0
        elif quarter in "AB":
            index = 1
        else:
            index = 2

        color_matrix = self.color_matrices[index]
        color_matrix = np.roll(color_matrix, shift=self.roll, axis=0)
        out_matrix_rgb = np.where(color_matrix[..., None].repeat(3, axis=2) == 0, in_matrix_color1, in_matrix_color2)
        return out_matrix_rgb

    def on_delete(self):
        pass
