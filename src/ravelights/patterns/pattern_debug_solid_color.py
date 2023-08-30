from ravelights.core.colorhandler import Color
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

    def render(self, colors: list[Color]):
        matrix = self.get_float_matrix_1d_mono()
        matrix[:] = 1.0
        matrix_rgb = self.colorize_matrix(matrix, color=colors[1])
        return matrix_rgb
