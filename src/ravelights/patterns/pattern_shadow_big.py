import math

import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern


class PatternShadowBig(Pattern):
    """pattern name: p_shadow"""

    def init(self):
        self.p_add_dimmer = 0.0
        self.p_add_thinner = 0.0

        self.width = 2

        self.pos = 0
        self.vel = 1

        self.dist_light = 1
        self.dist_gutter = 0.1
        self.dist_screen = 2

        self.grid_n = 20
        self.gutter = np.linspace(0, self.n_leds - 1, self.grid_n)

        self.max_dist = 100

    def alternate(self):
        ...

    def reset(self):
        self.pos = -self.max_dist

    def on_trigger(self):
        ...

    def render(self, colors: list[Color]) -> ArrayFloat:
        self.pos = self.pos + self.vel
        if self.pos > self.n_leds + self.max_dist:
            self.pos = -self.max_dist

        matrix = self.get_float_matrix_rgb()

        for index in range(self.grid_n - 1):
            poleA = self.gutter[index]
            poleB = self.gutter[index + 1]
            middle = (poleB + poleA) / 2
            dist = abs(self.pos - middle)

            if self.pos < poleA:
                alpha = math.atan((poleA - self.pos) / self.dist_light)
                projection_A = poleA + math.tan(alpha) * (self.dist_screen + self.dist_gutter)
            else:
                alpha = math.atan((poleA - self.pos) / (self.dist_light + self.dist_gutter))
                projection_A = poleA + math.tan(alpha) * self.dist_screen
            projection_A = max(0, projection_A)

            if self.pos < poleB:
                beta = math.atan((poleB - self.pos) / (self.dist_light + self.dist_gutter))
                projection_B = poleB + math.tan(beta) * self.dist_screen
            else:
                beta = math.atan((poleB - self.pos) / (self.dist_light))
                projection_B = poleB + math.tan(beta) * (self.dist_screen + self.dist_gutter)

            pax_int = int(round(projection_A))
            pbx_int = int(round(projection_B))
            # green:
            if pbx_int > 0:
                matrix[pax_int : pbx_int + 1, 0, 1] += 1 / (dist * 0.1)
            # blue:
            matrix[int(round(poleA)), 1, 2] += 0.2
            matrix[int(round(poleB)), 1, 2] += 0.2
            # red, x:
            matrix[self.pos : self.pos + self.width, 2, 0] = 1.0

        matrix = np.fmin(1.0, matrix)
        return matrix
        # matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        # matrix[start:end, :] = 1
        # return matrix_rgb
