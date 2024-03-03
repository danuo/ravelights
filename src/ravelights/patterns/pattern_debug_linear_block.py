from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern


class PatternDebugLinearBlock(Pattern):
    def init(self):
        self.p_add_thinner = 0.0
        self.p_add_dimmer = 0.0
        self.vel = 1
        self.size = 10

    def alternate(self):
        ...

    def reset(self):
        self.pos = 0

    def on_trigger(self):
        ...

    def render(self, colors: tuple[Color, Color]) -> ArrayFloat:
        self.pos = (self.pos + self.vel) % self.n_leds
        matrix = self.get_float_matrix_2d_mono()
        matrix[self.pos : self.pos + self.size, :] = 1
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
