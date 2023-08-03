from ravelights.core.colorhandler import Color
from ravelights.core.generator_super import Pattern


class PatternSolidColor(Pattern):
    """pattern name: p_solid_color"""

    def init(self):
        self.p_add_thinner = 1.0
        self.p_add_dimmer = 1.0

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, color: Color):
        matrix = self.get_float_matrix_1d_mono()
        matrix[:] = 1.0
        matrix_rgb = self.colorize_matrix(matrix, color=color)
        return matrix_rgb
