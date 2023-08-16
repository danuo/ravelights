import random

import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayNx3
from ravelights.core.generator_super import Pattern
from ravelights.core.pid import PIDController
from ravelights.core.utils import lerp


class PatternSinwave(Pattern):
    """pattern name: p_sinwave"""

    def init(self):
        self.static_x = 0
        self.eval_points = np.linspace(-1, 1, self.n_lights)
        self.bounds = 100
        self.width = 3

    def alternate(self):
        self.use_static = random.random() > 0.5
        self.use_static = False
        self.factors = np.random.random(5) * 0.5

    def reset(self):
        ...

    def on_trigger(self):
        ...

    @property
    def energy(self):
        """
        0.1 -> 0.1
        0.2 -> 0.2
        0.5 -> 0.5
        0.6 -> 0.9
        1.0 -> 2.0
        """
        energy_factor = self.settings.global_energy + 0.05
        if energy_factor > 0.5:
            energy_factor = 0.5 + (energy_factor - 0.5) * 5
        return energy_factor

    def get_square_positions(self):
        self.static_x += 5
        if self.static_x < -self.bounds:
            self.static_x = self.static_x + self.n_leds + 2 * self.bounds
        if self.static_x > self.n_leds + self.bounds:
            self.static_x = self.static_x - self.n_leds - 2 * self.bounds

        out = self.factors[0] * np.sin(0.25 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy)
        out = self.factors[1] * np.sin(0.5 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy)
        out += self.factors[2] * np.sin(1 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy)
        out += self.factors[3] * np.sin(2 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy)
        out += self.factors[4] * np.sin(4 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy)
        out = out * self.n_leds * 0.5 + self.n_leds * 0.5
        if self.use_static:
            out += self.static_x
        out = np.round(out).astype(int)
        return out

    def render(self, color: Color) -> ArrayNx3:
        out = self.get_square_positions()
        matrix = self.get_float_matrix_2d_mono()
        for i in range(self.n_lights):
            pos = out[i]
            if pos > 0:
                matrix[pos : pos + self.width, i] = 1
        matrix_rgb = self.colorize_matrix(matrix, color=color)
        return matrix_rgb
