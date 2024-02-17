from ravelights.core.color_handler import Color, ColorHandler
from ravelights.core.custom_typing import Array
from ravelights.core.generator_super import Vfilter


class VfilterBW(Vfilter):
    "name = v_bw"

    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    @staticmethod
    def render(in_matrix: Array, colors: tuple[Color, Color]) -> Array:
        if in_matrix.ndim == 3:
            in_matrix_rgb = in_matrix.reshape(-1, 3, order="F")
            luminance = ColorHandler.rgb_to_brightness(in_matrix_rgb)
            in_matrix_rgb = luminance[:, None].repeat(repeats=3, axis=1)
            return in_matrix_rgb.reshape(in_matrix.shape, order="F")
        assert False
