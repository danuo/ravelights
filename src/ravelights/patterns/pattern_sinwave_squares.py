import math
import random

import numpy as np
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat, ArrayInt
from ravelights.core.generator_super import Pattern


class ModdedInerseSquare:
    def __init__(self, n_leds: int):
        self.n_leds = n_leds
        self.square_baselength = 20
        self.arm_length = 25
        self.n_anker = 10
        self.anker_gap = 0
        self.anker_positions = np.linspace(self.anker_gap, self.n_leds - self.anker_gap, self.n_anker)  # have many
        self.influence = 20

    def render_matrix(self, pos: int | float):
        pos = int(round(pos))

        matrix = np.zeros(self.n_leds)
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


class PatternSinwaveSquares(Pattern):
    def init(self):
        self.renderer = ModdedInerseSquare(self.n_leds)
        self.static_x = 0
        self.eval_points = np.linspace(-1, 1, self.n_lights)
        self.bounds = 100
        self.width = 3

    def alternate(self):
        self.use_static = random.random() > 0.5
        self.use_static = True
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

    def get_square_positions(self) -> ArrayInt:
        self.static_x += 5
        if self.static_x < -self.bounds:
            self.static_x = self.static_x + self.n_leds + 2 * self.bounds
        if self.static_x > self.n_leds + self.bounds:
            self.static_x = self.static_x - self.n_leds - 2 * self.bounds

        out: ArrayFloat = self.factors[0] * np.sin(
            0.25 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy
        )
        out += self.factors[1] * np.sin(0.5 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy)
        out += self.factors[2] * np.sin(1 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy)
        out += self.factors[3] * np.sin(2 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy)
        # out += self.factors[4] * np.sin(4 * self.eval_points + self.settings.timehandler.time_0 * 2 * self.energy)
        out = out * self.n_leds * 0.5 + self.n_leds * 0.5
        if self.use_static:
            out += self.static_x
        return np.round(out).astype(int)

    def render(self, colors: list[Color]) -> ArrayFloat:
        out = self.get_square_positions()
        matrix = self.get_float_matrix_2d_mono()
        for i in range(self.n_lights):
            matrix[..., i] = self.renderer.render_matrix(out[i])
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
