import random

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern


class Horbar:
    def __init__(self, pat: Pattern):
        self.pos = random.randrange(pat.n_leds)
        self.height = random.randrange(1, 10)
        self.speed = random.choice([-2, -1, 1, 2])
        self.light = random.randrange(1, pat.n_lights + 1)
        self.width = random.randrange(1, pat.n_lights + 1)
        if random.random() > 0.5:
            self.light = max(0, self.light - self.width)


class PatternHorStripes(Pattern):
    def init(self):
        self.p_add_thinner = 0.5
        self.p_add_dimmer = 0.5

    def alternate(self):
        ...

    def reset(self):
        self.items: list[Horbar] = []

    def on_trigger(self):
        for _ in range(random.randrange(1, 4)):
            self.items.append(Horbar(self))

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        matrix = self.get_float_matrix_2d_mono()
        for item in self.items:
            item.pos += item.speed
            matrix[item.pos : item.pos + item.height, item.light : item.light + item.width] = 1.0
        return self.colorize_matrix(matrix, color=colors[0])
