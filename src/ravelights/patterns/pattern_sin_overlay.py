import math

from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern


class PatternSinOverlay(Pattern):
    def init(self):
        self.p_add_thinner = 0.0
        self.p_add_dimmer = 0.0
        self.vel = 1
        self.size = 10

        self.dist1 = 5
        self.dist2 = 10
        self.dist3 = 15
        self.width = 1

    def alternate(self):
        ...

    def reset(self):
        self.pos = 50

    def on_trigger(self):
        ...

    def render(self, colors: tuple[Color, Color]) -> ArrayFloat:
        time = self.timehandler.time_0
        matrix = self.get_float_matrix_2d_mono()
        self.pos = (self.pos + self.vel) % self.n_leds

        # render 1
        a = int(self.pos - self.dist1 * abs(math.sin(time)))
        b = int(self.pos + self.dist1 * abs(math.sin(time)))
        matrix[a : a + self.width, :] = 1
        matrix[b : b + self.width, :] = 1

        # render 2
        a = int(a - self.dist2 * abs(math.sin(5 * time)))
        b = int(b + self.dist2 * abs(math.sin(5 * time)))
        matrix[a : a + self.width, :] = 0.7
        matrix[b : b + self.width, :] = 0.7

        # render 3
        a = int(a - self.dist3 * abs(math.sin(10 * time)))
        b = int(b + self.dist3 * abs(math.sin(10 * time)))
        matrix[a : a + self.width, :] = 0.4
        matrix[b : b + self.width, :] = 0.4

        # render
        a = int(a - self.dist3 * abs(math.sin(30 * time)))
        b = int(b + self.dist3 * abs(math.sin(30 * time)))
        matrix[a : a + self.width, :] = 0.2
        matrix[b : b + self.width, :] = 0.2
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
