import random

import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array
from ravelights.effects.effect_super import Effect


class EffectColorize(Effect):
    def reset(self):
        """
        hue_range controls the color variation for each frame
        """

        self.color_matrix = np.zeros(shape=(self.n_leds, self.n_lights), dtype=int)

        self.mode = random.choice(["up_down", "blocks"])
        self.mode = "blocks"
        match self.mode:
            case "up_down":
                # demo color segmentation
                self.color_matrix[:70, :] = 1
            case "blocks":
                i = 0
                sign = False
                # self.color_matrix = self.color_matrix.flatten()
                print(self.color_matrix.shape)
                while i < self.n:
                    number = random.randint(5, 50)
                    self.color_matrix[i : i + number] = sign
                    sign = not sign
                    i += number
                # self.color_matrix = self.color_matrix.reshape((self.n_leds, self.n_lights))

    def run_before(self):
        ...

    def run_after(self):
        ...

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        # bw filter
        in_matrix_bw = np.max(in_matrix, axis=-1)

        color_1, color_2, color_effect = self.settings.color_engine.get_colors_rgb(timeline_level=1)
        in_matrix_color1 = self.colorize_matrix(in_matrix_bw, color=color_1)
        in_matrix_color2 = self.colorize_matrix(in_matrix_bw, color=color_2)
        out_matrix_rgb = np.where(self.color_matrix[..., None].repeat(3, axis=2) == 1, in_matrix_color1, in_matrix_color2)
        return out_matrix_rgb

    def on_delete(self):
        pass
