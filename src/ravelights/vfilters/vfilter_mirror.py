import numpy as np
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Vfilter


class VfilterMirrorVer(Vfilter):
    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    @staticmethod
    def render(in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        matrix: ArrayFloat = in_matrix
        if in_matrix.ndim == 1:
            # shape is (n_leds) == Nx1
            n = in_matrix.shape[0] // 2
            matrix_mirrored = np.flip(in_matrix, axis=0)
            matrix[n:] = matrix_mirrored[n:]
        elif in_matrix.ndim == 2:  # shape is (n, 3)
            # todo: test this case
            assert False
            matrix = in_matrix
            n = matrix.shape[0] // 2
            matrix_mirrored = np.flip(matrix, axis=0)
            matrix[n:, :, :] = matrix_mirrored[n:, :, :]
        elif in_matrix.ndim == 3:
            # shape is (n_leds, n_lights, 3) == Nx3
            n = in_matrix.shape[0] // 2
            matrix_mirrored = np.flip(in_matrix, axis=0)
            matrix[n:, :, :] = matrix_mirrored[n:, :, :]
        return matrix
