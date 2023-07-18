# flash upwords

import math
import random

import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.utils import i_to_rgb, p, sign


class MovingStrobeLegacy:
    def __init__(self, n_lights, n_leds):
        self.p_bigstrobe: float = 0.1
        self.p_distort: float = 0.0  # will be randomized later
        self.p_pause: float = 0.3
        self.p_thin: float = 0.9
        self.pos: int = 0
        self.error: int = 0
        self.speed: int = 0
        self.length: int = 0
        self.max_frame: int = 0
        self.error_speed: float = 0
        self.sin_factor: float = 2.0
        self.n_lights: int = n_lights
        self.n_leds: int = n_leds
        self.n: int = n_lights * n_leds
        self.mode_random_direction: bool = True
        self.mode_bigstrobe: bool = False
        self.mode_pause: bool = False
        self.mode_thinned: bool = False
        self.reset()

    def reset(self):
        self.p_distort = random.uniform(0.1, 0.75)
        self.light = random.randrange(start=0, stop=self.n_lights)
        self.frame = 0
        self.pos = int(abs(random.gauss(mu=0, sigma=1) * self.n))
        self.pos = max(self.pos, 1)
        self.error = 0
        self.speed = random.randrange(start=1, stop=5)
        self.length = random.randrange(start=5, stop=50)  # prev: 2,25
        self.max_frame = random.randrange(start=5, stop=40)  # prev: 5, 30
        self.error_speed = random.gauss(mu=2, sigma=0.5)
        self.error_speed = max(self.error_speed, 0.5)
        self.mode_bigstrobe = False
        self.mode_pause = False

        # special mode: bigstrobe
        if p(self.p_bigstrobe):
            self.mode_bigstrobe = True
            self.max_frame = random.randrange(start=2, stop=9)

        # special mode: thinned LED
        self.mode_thinned = False
        self.thinning = 3  # ! is 3
        if p(self.p_thin):
            self.mode_thinned = True

        # special mode: pause
        if p(self.p_pause):
            self.mode_pause = True
            self.max_frame = 10

    def render(self, color: Color):
        matrix = np.zeros(shape=(self.n_lights * self.n_leds), dtype=float)

        self.frame += 1
        # see if animation is finished
        if self.frame > self.max_frame:
            self.reset()

        if self.mode_pause:
            return i_to_rgb(matrix, Color(1, 0, 0))  # todo: matrix needs to be int

        # apply direction
        if self.mode_random_direction:
            direction = 1 if p(0.5) else -1
        else:
            direction = 1

        # get intensity
        intens = abs(math.sin(self.frame * self.sin_factor)) + 0.1
        intens = min(intens, 1)

        # update position
        pos = direction * int(self.pos + self.error)
        if pos < 0:
            pos += self.n_leds
        self.pos += self.speed
        if self.pos > self.n_leds:
            self.reset()
        self.error = -sign(self.error) * (abs(self.error) + self.error_speed)

        # apply pixel range
        offset = self.light * self.n_leds
        a = int(max(0, pos)) + offset
        b = int(min(self.n_leds, pos + self.length)) + offset
        b = int(max(b, 1))
        if a >= b:
            a = b - 1

        # bigstrobe
        if self.mode_bigstrobe:
            borders = (random.randrange(0, self.n), random.randrange(0, self.n))
            a = min(borders)
            b = max(borders)

        # global distortion
        for i in range(a, b):
            if self.mode_thinned:
                if i % self.thinning in random.choices(range(self.thinning), k=self.thinning - 1):
                    # do nothing
                    continue
            if p(self.p_distort):
                matrix[i] = 0
            else:
                matrix[i] = intens

        return i_to_rgb(matrix, Color(1, 0, 0))  # todo: matrix needs to be int
