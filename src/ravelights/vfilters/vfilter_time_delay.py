import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array, ArrayMxKx3, ArrayNx1
from ravelights.core.generator_super import Vfilter


class VfilterTimeDelay(Vfilter):
    def init(self):
        self.mode = 3  # modes 1,2,3,4 implemented
        self.delay_steps = 3
        self.mem_length = self.n_lights * self.delay_steps + 1
        self.memory_matrix = np.zeros((self.n_leds, self.n_lights, 3, self.mem_length))  # this is 4d, can be 3d too
        self.zero_index = 0

    def alternate(self):
        ...

    def reset(self):
        self.memory_matrix[...] = 0.0
        self.zero_index = 0

    def on_trigger(self):
        ...

    def render(self, in_matrix: Array, colors: list[Color]) -> Array:
        self.memory_matrix[..., self.zero_index] = in_matrix

        out_matrix = self.get_float_matrix_rgb()

        if self.mode in [0, 1]:
            for light_index in range(self.n_lights):  # 0, 1, 2
                time_index = self.zero_index - (self.delay_steps * light_index)
                if self.mode == 0:  # left to right
                    pass
                if self.mode == 1:  # right to left
                    light_index = -1 - light_index
                out_matrix[:, light_index, :] = self.memory_matrix[:, 0, :, time_index]
        if self.mode in [2, 3]:
            if self.mode == 2 and (self.n_lights % 2 == 1):  # mid to outer
                middle_index = self.n_lights // 2
                custom_delay = self.zero_index - self.delay_steps * middle_index
                out_matrix[:, middle_index, :] = self.memory_matrix[:, 0, :, custom_delay]
            if self.mode == 3 and (self.n_lights % 2 == 1):  # mid to outer
                middle_index = self.n_lights // 2
                custom_delay = self.zero_index
                out_matrix[:, middle_index, :] = self.memory_matrix[:, 0, :, custom_delay]
            for light_index in range(self.n_lights // 2):  # 0, 1, 2
                if self.mode == 2:
                    time_index = self.zero_index - (self.delay_steps * light_index)
                if self.mode == 3:
                    time_index = self.zero_index - (self.delay_steps * (1 + light_index))
                    light_index = self.n_lights // 2 - light_index - 1
                light_index_sec = -1 - light_index
                out_matrix[:, light_index, :] = self.memory_matrix[:, 0, :, time_index]
                out_matrix[:, light_index_sec, :] = self.memory_matrix[:, 0, :, time_index]

        self.zero_index = (self.zero_index + 1) % self.mem_length
        return out_matrix
