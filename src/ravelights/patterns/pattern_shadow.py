import math
import random

import numpy as np

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.generator_super import Pattern
from ravelights.core.pid import PIDController
from ravelights.core.utils import lerp


class PatternShadow(Pattern):
    """pattern name: p_shadow"""

    def init(self):
        self.p_add_dimmer = 0.5
        self.p_add_thinner = 0.5

        self.pids = [PIDController(kp=0.5, kd=0.1, dt=self.settings.frame_time) for _ in range(self.n_lights)]
        for pid in self.pids:
            pid.load_parameter_preset("slow")
        self.width = 2
        # self.pos = 0
        self.vel = 1
        self.dist_light = 0.7
        self.dist_gutter = 0.3
        self.dist_screen = 1.5
        self.grid_n = 30
        self.gutter = np.linspace(0, self.n_leds - 1, self.grid_n)
        self.max_dist = 50

        # ─── New ──────────────────────────────────────────────────────

        self.possible_triggers = [BeatStatePattern(loop_length=4)]
        self.pos: list[float | int] = [0] * self.n_lights
        self.speeds: list[float | int] = [0] * self.n_lights
        self.bounds: int = 50
        self.on_trigger()

    def alternate(self):
        self.mode = random.choice([0, 1])
        self.speeds = [random.uniform(-10, 10) for _ in range(self.n_lights)]

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

    def render_shadow(self, pos: int | float):
        matrix = np.zeros((self.n_leds,))

        for index in range(self.grid_n - 1):
            poleA = self.gutter[index]
            poleB = self.gutter[index + 1]
            middle = (poleB + poleA) / 2
            dist: int | float = abs(pos - middle)

            if pos < poleA:
                alpha = math.atan((poleA - pos) / self.dist_light)
                projection_A = poleA + math.tan(alpha) * (self.dist_screen + self.dist_gutter)
            else:
                alpha = math.atan((poleA - pos) / (self.dist_light + self.dist_gutter))
                projection_A = poleA + math.tan(alpha) * self.dist_screen
            projection_A = max(0, projection_A)

            if pos < poleB:
                beta = math.atan((poleB - pos) / (self.dist_light + self.dist_gutter))
                projection_B = poleB + math.tan(beta) * self.dist_screen
            else:
                beta = math.atan((poleB - pos) / (self.dist_light))
                projection_B = poleB + math.tan(beta) * (self.dist_screen + self.dist_gutter)

            pax_int = int(round(projection_A))
            pbx_int = int(round(projection_B))

            if pbx_int > 0:
                matrix[pax_int : pbx_int + 1] += 1 / (dist * 0.1)
        return matrix

    def render(self, colors: list[Color]):
        self.perform_pid_steps()
        matrix = self.get_float_matrix_2d_mono()
        for index in range(self.n_lights):
            if self.mode == 0:
                speed = self.speeds[index]
            else:  # self.mode == 1
                speed = self.pids[index].value * 0.1

            self.pos[index] += speed
            if self.pos[index] < -self.bounds:
                self.pos[index] = self.pos[index] + self.n_leds + 2 * self.bounds
            if self.pos[index] > self.n_leds + self.bounds:
                self.pos[index] = self.pos[index] - self.n_leds - 2 * self.bounds

            pos = int(round(self.pos[index]))
            matrix[:, index] = self.render_shadow(pos)

        matrix = np.fmin(1.0, matrix)
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
