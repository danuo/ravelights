import random

import numpy as np
from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern
from ravelights.core.pid import PIDController
from ravelights.core.utils import lerp


class PatternPID(Pattern):
    """pattern name: p_pid"""

    def init(self):
        self.width = 20
        self.pids = [PIDController(kp=0.5, kd=0.1, dt=self.settings.frame_time) for _ in range(self.n_lights)]

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
        for pid in self.pids:
            pid.target = random.randrange(0, self.n_leds)

    def perform_pid_steps(self):
        for pid in self.pids:
            # dynamic kd
            pid.kp = lerp(self.settings.global_energy, 0.1, 1.0)
            pid.kd = lerp(self.settings.global_energy, 0.05, 0.15)
            pid.perform_pid_step()

    def render(self, colors: list[Color]) -> ArrayFloat:
        self.perform_pid_steps()
        matrix = self.get_float_matrix_2d_mono()
        for index in range(self.n_lights):
            pos = int(self.pids[index].value)
            start = np.clip(pos - self.width // 2, 0, self.n_leds - 1)
            end = np.clip(pos + self.width // 2, 0, self.n_leds)

            matrix[start:end, index] = 1
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
