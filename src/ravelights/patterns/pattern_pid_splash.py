import random

import numpy as np

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.generator_super import Pattern
from ravelights.core.pid import PIDController
from ravelights.core.utils import lerp


class PatternPidSplash(Pattern):
    """pattern name: p_pid_splash"""

    def init(self):
        self.width = 10
        tp = 1
        dt = 1 / 50
        td = 0.5 * dt
        ti = min(8 * dt, tp)
        kp = 0.5 * tp / (td)
        self.pid = PIDController(kp=kp, kd=td, ki=ti, dt=dt)
        self.counter_frames = 0

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
        self.counter_frames = 0
        start_pos = random.randrange(20, self.n_leds // 2)
        end_pos = self.n_leds - start_pos
        error = end_pos - start_pos
        start_vel = error * 0.075
        self.pid._x = start_pos
        self.pid._dx = start_vel
        self.pid.target = end_pos
        self.pid._previous_error = (error) * 1.5

    def render(self, colors: list[Color]):
        if self.counter_frames == 0:
            intensity = 0.2
        elif self.counter_frames == 1:
            intensity = 0.6
        else:
            intensity = 1.0 - self.settings.beat_progress
        self.counter_frames += 1
        # dynamic kd
        self.pid.kp = lerp(self.settings.global_energy, 0.1, 1.0)
        self.pid.kd = lerp(self.settings.global_energy, 0.05, 0.15)
        self.pid.perform_pid_step()
        self.pid.perform_pid_step()
        self.pid.perform_pid_step()
        self.pid.perform_pid_step()
        self.pid.perform_pid_step()
        pos = int(self.pid.value)
        start = np.clip(pos - self.width // 2, 0, self.n_leds - 1)
        end = np.clip(pos + self.width // 2, 0, self.n_leds - 1)

        matrix = self.get_float_matrix_2d_mono()
        matrix[start:end, :] = intensity
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
