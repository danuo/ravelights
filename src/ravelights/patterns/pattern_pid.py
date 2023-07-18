import random

import numpy as np

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayNx1, ArrayNx3
from ravelights.core.generator_super import Pattern
from ravelights.core.pid import PIDController
from ravelights.core.utils import lerp


class PatternPID(Pattern):
    """pattern name: p_pid"""

    def init(self):
        self.width = 20
        self.pid = PIDController(kp=0.5, kd=0.1, dt=self.settings.frame_time)

    @property
    def possible_triggers(self) -> list[BeatStatePattern]:
        if self.settings.global_energy >= 0.5:
            return [BeatStatePattern(loop_length=1)]
        else:
            return [BeatStatePattern(loop_length=4)]

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        self.pid.target = random.randrange(0, self.n_leds)

    def render(self, color: Color) -> ArrayNx3:
        # dynamic kd
        self.pid.kp = lerp(self.settings.global_energy, 0.1, 1.0)
        self.pid.kd = lerp(self.settings.global_energy, 0.05, 0.15)
        self.pid.perform_pid_step()
        pos = int(self.pid.value)
        start = np.clip(pos - self.width // 2, 0, self.n_leds - 1)
        end = np.clip(pos + self.width // 2, 0, self.n_leds - 1)

        matrix = self.get_float_matrix_2d_mono()
        matrix[start:end, :] = 1
        matrix_rgb = self.colorize_matrix(matrix, color=color)
        return matrix_rgb
