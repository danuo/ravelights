import numpy as np
from icecream import ic

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
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

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        # bw
        # color = np.asanyarray(colors[0])
        bw_matrix_mono = self.bw_matrix(in_matrix)

        # get color
        # todo: cleanup
        rgb_sum = np.sum(in_matrix, axis=-1).reshape((-1))
        max_id = np.argmax(rgb_sum)
        # ! still bugged!
        if rgb_sum[max_id] == 0:
            return in_matrix
        else:
            color = in_matrix.reshape(-1, 3, order="F")
            # print(in_matrix.reshape(-1, 3, order="F")[:10])
            ic(np.max(color).shape)
            divisor = np.max(color, axis=-1)
            non_zero_divisor = np.fmin(0.0001, divisor)
            color = color / non_zero_divisor[..., None]
            # ! bug. should divide through np.max of that line, not np.max from total
            color = np.fmin(1, color)
        # ic(color.shape)

        # find edge
        roll = np.roll(bw_matrix_mono, shift=1, axis=0)
        roll[0] = 0  # does this work?
        diff = np.abs(bw_matrix_mono - roll)

        ic(color.shape)
        ic(color[10:])

        if self.version == 0:
            ic(diff.shape)
            ic(color.shape)
            # return self.colorize_matrix(diff, color)
            return diff[..., None] * color.reshape((self.n_leds, self.n_lights, 1))

        # expand
        self.expansion_matrix[..., 0] = diff
        for i in range(self.n_exp):
            roll = np.roll(diff, shift=i + 1, axis=0)  # 1 2 3
            roll[0] = 0
            self.expansion_matrix[..., 2 * i + 1] = roll  # 1, 3, 5

            roll = np.roll(diff, shift=-i - 1, axis=0)  # -1 -2 -3
            roll[-1] = 0
            self.expansion_matrix[..., 2 * i + 2] = roll  # 2, 4, 6

        bw_out = np.max(self.expansion_matrix, axis=-1)

        ic(bw_out.shape)
        return bw_out[..., None] * color.reshape((self.n_leds, self.n_lights, 3))
