import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayMxKx3
from ravelights.core.generator_super import Vfilter


class VfilterEdgedetect(Vfilter):
    """versions: 0, 1, 2"""

    def init(self):
        self.n_exp = 0
        if self.version == 1:
            self.n_exp = 1
        if self.version == 2:
            self.n_exp = 2
        self.expansion_matrix = np.zeros((self.n_leds, self.n_lights, 1 + (2 * self.n_exp)))
        self.version = 1

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayMxKx3, color: Color) -> ArrayMxKx3:
        # bw
        color = np.asanyarray(color)
        bw_matrix_mono = self.bw_matrix(in_matrix)

        # get color
        # todo: cleanup
        rgb_sum = np.sum(in_matrix, axis=-1).reshape((-1))
        max_id = np.argmax(rgb_sum)
        if rgb_sum[max_id] > 0:
            color = in_matrix.reshape(-1, 3, order="F")[max_id]
            color = color / np.max(color)
            color = np.fmin(1, color)

        # find edge
        roll = np.roll(bw_matrix_mono, shift=1, axis=0)
        roll[0] = 0  # does this work?
        diff = np.abs(bw_matrix_mono - roll)

        if self.version == 0:
            return self.colorize_matrix(diff, color)

        # expand
        self.expansion_matrix[..., 0] = diff
        for i in range(self.n_exp):
            roll = np.roll(diff, shift=i + 1, axis=0)  # 1 2 3
            roll[0] = 0
            self.expansion_matrix[..., 2 * i + 1] = roll  # 1, 3, 5

            roll = np.roll(diff, shift=-i - 1, axis=0)  # -1 -2 -3
            roll[-1] = 0
            self.expansion_matrix[..., 2 * i + 2] = roll  # 2, 4, 6

        return self.colorize_matrix(np.max(self.expansion_matrix, axis=-1), color)
