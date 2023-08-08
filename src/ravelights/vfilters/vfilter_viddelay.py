import numpy as np


class videodelay:
    # todo: finish
    def __init__(self, in_matrix):
        self.memory_len = 3
        self.memory_matrix = np.zeros((*in_matrix.shape, self.memory_len))
        self.intensity = np.zeros(in_matrix.shape)

    def render(self, in_matrix):
        def intensity_step(prev_intensity):
            return min(1.0, 0.2 + prev_intensity * 2)

        self.memory_matrix = np.roll(self.memory_matrix, shift=1, axis=-1)
        self.memory_matrix[..., 0] = in_matrix
        intensity_target = np.max(self.memory_matrix, axis=-1)

        # idea. a pixel hat has i=0 can only grow to i = 0.2
        # 0.2 -> 0.7
        # 0.5 -> 1
