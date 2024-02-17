import math
import random

import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern


class PatternInerseSquare(Pattern):
    def init(self):
        self.p_add_thinner = 0.1
        self.p_add_dimmer = 0.1
        self.pos = 0
        self.bounds = 50
        self.square_baselength = 20
        self.arm_length = 25
        self.n_anker = 10
        self.anker_gap = 0
        self.anker_positions = np.linspace(self.anker_gap, self.n_leds - self.anker_gap, self.n_anker)  # have many
        self.influence = 20

    def alternate(self):
        self.mode = random.choice([0, 1])

    def reset(self):
        ...

    def on_trigger(self):
        ...

    @property
    def speed(self):
        return 3 * 2 * self.settings.global_energy

    def render_thing(self, pos: float):
        pos = int(round(pos))
        matrix = np.zeros((self.n_leds,))
        for anker_pos in self.anker_positions:
            diff = pos - anker_pos
            dist = min(abs(diff), self.influence) / self.influence
            if diff > 0:
                square_pos = anker_pos - self.arm_length * math.sin(dist * math.pi / 1.3)
            else:
                square_pos = anker_pos + self.arm_length * math.sin(dist * math.pi / 1.3)
            square_pos = int(round(square_pos))
            square_length = int(self.square_baselength * (3 + dist**2) / 3) // 2
            intensity = 1 - dist**2
            a = square_pos - square_length
            b = square_pos + square_length
            a = max(0, a)
            if b < 0:
                continue
            matrix[a:b] = intensity
        return matrix

    def render(self, colors: tuple[Color, Color]) -> ArrayFloat:
        self.pos += self.speed
        if self.pos < -self.bounds:
            self.pos = self.pos + self.n_leds + 2 * self.bounds
        if self.pos > self.n_leds + self.bounds:
            self.pos = self.pos - self.n_leds - 2 * self.bounds

        matrix = self.get_float_matrix_2d_mono()
        for index in range(self.n_lights):
            if self.mode == 0:
                pos = self.pos
            elif self.mode == 1:
                if index % 2 == 0:
                    pos = self.pos
                else:
                    pos = self.n_leds - self.pos
            matrix[:, index] = self.render_thing(pos)

        return self.colorize_matrix(matrix, color=colors[0])
