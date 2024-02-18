from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern


class PatternDebugSolidColor(Pattern):
    """pattern name: p_solid_color"""

    def init(self):
        self.p_add_thinner = 0.0
        self.p_add_dimmer = 0.0

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, colors: tuple[Color, Color]) -> ArrayFloat:
        matrix_1d = self.get_float_matrix_1d_mono()
        matrix_1d[:] = 1.0
        matrix_rgb = self.colorize_matrix(self.reshape_1d_to_2d(matrix_1d), color=colors[0])
        return matrix_rgb
