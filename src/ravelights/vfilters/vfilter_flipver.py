import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Vfilter


class VfilterFlipVer(Vfilter):
    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        if in_matrix.ndim == 1:
            matrix: ArrayFloat = np.flip(in_matrix, axis=0)  # Nx1
        elif in_matrix.ndim == 2:
            # todo: implement if needed
            assert False
            matrix = np.flip(matrix, axis=0)
        elif in_matrix.ndim == 3:
            matrix: ArrayFloat = np.flip(in_matrix, axis=0)  # Nx3
        return matrix
