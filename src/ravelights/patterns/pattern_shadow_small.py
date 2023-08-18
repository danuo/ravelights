import math
import random

import numpy as np

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayNx1, ArrayNx3
from ravelights.core.generator_super import Pattern
from ravelights.core.pid import PIDController
from ravelights.core.utils import lerp


class PatternShadowSmall(Pattern):
    """pattern name: p_shadow"""

    def init(self):
        self.p_add_dimmer = 0.0
        self.p_add_thinner = 0.0

        self.width = 2

        self.pos = 0
        self.vel = 1

        self.dist_light = 0.7
        self.dist_gutter = 0.3
        self.dist_screen = 1.5

        self.grid_n = 30
        self.gutter = np.linspace(0, self.n_leds - 1, self.grid_n)

        self.max_dist = 50

    def alternate(self):
        ...

    def reset(self):
        self.pos = -self.max_dist

    def on_trigger(self):
        ...

    def render(self, color: Color) -> ArrayNx3:
        self.pos = self.pos + self.vel
        matrix = self.get_float_matrix_2d_mono()
        for light_index in range(self.n_lights):
            pos = self.pos
            if pos > self.n_leds + self.max_dist:
                pos = -self.max_dist

            for index in range(self.grid_n - 1):
                poleA = self.gutter[index]
                poleB = self.gutter[index + 1]
                middle = (poleB + poleA) / 2
                dist = abs(pos - middle)

                if pos < poleA:
                    alpha = math.atan((poleA - pos) / self.dist_light)
                    projection_A = poleA + math.tan(alpha) * (self.dist_screen + self.dist_gutter)
                else:
                    alpha = math.atan((poleA - pos) / (self.dist_light + self.dist_gutter))
                    projection_A = poleA + math.tan(alpha) * self.dist_screen
                projection_A = max(0, projection_A)

                if pos < poleB:
                    beta = math.atan((poleB - pos) / (self.dist_light + self.dist_gutter))
                    projection_B = poleB + math.tan(beta) * self.dist_screen
                else:
                    beta = math.atan((poleB - pos) / (self.dist_light))
                    projection_B = poleB + math.tan(beta) * (self.dist_screen + self.dist_gutter)

                pax_int = int(round(projection_A))
                pbx_int = int(round(projection_B))
                # green:
                if pbx_int > 0:
                    matrix[pax_int : pbx_int + 1, light_index] += 1 / (dist * 0.1)

        matrix = np.fmin(1.0, matrix)
        matrix_rgb = self.colorize_matrix(matrix, color=color)
        return matrix_rgb
