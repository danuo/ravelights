import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array, ArrayMxKx3, ArrayNx1
from ravelights.core.generator_super import Vfilter


class VfilterMirror(Vfilter):
    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    @staticmethod
    def render(in_matrix: Array, color: Color) -> Array:
        if in_matrix.ndim == 1:  # shape is (n_leds)
            n = in_matrix.shape[0] // 2
            matrix: ArrayNx1 = in_matrix
            matrix_mirrored = np.flip(in_matrix, axis=0)
            matrix[n:] = matrix_mirrored[n:]
        elif in_matrix.ndim == 2:  # shape is (n, 3)
            # todo: test this case
            assert False
            matrix = in_matrix
            n = matrix.shape[0] // 2
            matrix_mirrored = np.flip(matrix, axis=0)
            matrix[n:, :, :] = matrix_mirrored[n:, :, :]
        elif in_matrix.ndim == 3:  # shape is (n_leds, n_lights, 3)
            matrix: ArrayMxKx3 = in_matrix
            n = in_matrix.shape[0] // 2
            matrix_mirrored = np.flip(in_matrix, axis=0)
            matrix[n:, :, :] = matrix_mirrored[n:, :, :]
        return matrix
