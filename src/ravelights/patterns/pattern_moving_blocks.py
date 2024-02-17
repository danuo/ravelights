import random
from dataclasses import astuple, dataclass

import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern
from ravelights.core.time_handler import BeatStatePattern
from ravelights.core.utils import p


@dataclass
class State:
    item_id: int
    bright: float
    pos: float
    speed: float

    def __iter__(self):
        return iter(astuple(self))


class PatternMovingBlocks(Pattern):
    """pattern name: p_moving_blocks"""

    def init(self):
        # prerendered items are larger than actual light, so that big items can fit
        self.matrix_length = self.n_leds * 3
        self.possible_triggers = [
            BeatStatePattern(beats=[0], loop_length=4),
            BeatStatePattern(beats=[0], quarters="A", loop_length=1),
            BeatStatePattern(beats=[0], quarters="AC", loop_length=1),
            BeatStatePattern(beats=[0], quarters="ABCD", loop_length=1),
        ]

    def alternate(self):
        self.version = random.choice([0, 1, 2, 3])
        # version = 0
        if self.version == 0:
            self.n_lengths = 10
            self.length_step_factor = 2
            self.max_speed = 4
            self.n_items = 10
            self.brightness = 1.0
            self.max_roll_speed = 5
        if self.version == 1:
            self.n_lengths = 8
            self.length_step_factor = 3
            self.max_speed = 3
            self.n_items = 15
            self.brightness = 1.0
            self.max_roll_speed = 5
        if self.version == 2:
            self.n_lengths = 10
            self.length_step_factor = 4
            self.max_speed = 0  # no speed but reset constantly
            self.n_items = 15
            self.brightness = 1.0
            self.max_roll_speed = 2
        if self.version == 3:
            self.n_lengths = 10
            self.length_step_factor = 4
            self.max_speed = 2
            self.n_items = 15
            self.brightness = 0.5
            self.max_roll_speed = 10

        self.enable_roll = p(0.5)

        # ─── Generate Prerendered Blocks ──────────────────────────────
        def sequence_func(num: int):
            num = int(num)
            while True:
                yield num
                num = int(num + num / self.length_step_factor)

        n_items = [next(sequence_func(4)) for _ in range(self.n_lengths)]
        self.prerendered_matrices: list[ArrayFloat] = []
        for length in n_items:
            matrix = np.zeros(shape=(self.matrix_length))
            a = int(self.matrix_length / 2 - length / 2)
            b = int(self.matrix_length / 2 + length / 2)
            matrix[a:b] = 1.0
            self.prerendered_matrices.append(matrix)
        self.reset()

    def reset(self):
        self.states: list[State] = []
        for _ in range(self.n_items):
            item_id = random.randrange(0, len(self.prerendered_matrices))
            bright = random.uniform(0, 1)
            pos = random.uniform(0, self.matrix_length)
            speed = 0 if self.max_speed == 0 else random.uniform(-self.max_speed, self.max_speed)
            self.states.append(State(item_id, bright, pos, speed))
        self.roll_speeds = [random.uniform(-self.max_roll_speed, self.max_roll_speed) for _ in range(self.n_lights)]
        self.rolls = [0.0] * self.n_lights

    def on_trigger(self):
        self.reset()

    def render(self, colors: tuple[Color, Color]) -> ArrayFloat:
        matrix = self.get_float_matrix_2d_mono()
        matrix = np.zeros((self.n_leds))
        for state in self.states:
            item_id, bright, pos, speed = state
            rolled_view: ArrayFloat = np.roll(self.prerendered_matrices[item_id], shift=int(pos))
            matrix[:] = matrix + self.brightness * bright * rolled_view[: self.pixelmatrix.n_leds]
            state.pos = state.pos + speed
        matrix = self.pixelmatrix.clip_matrix_to_1(matrix)
        matrix = np.repeat(matrix[..., None], repeats=self.n_lights, axis=-1)

        if self.enable_roll:
            for index in range(self.n_lights):
                self.rolls[index] += self.roll_speeds[index]
            for index in range(self.n_lights):
                roll = int(round(self.rolls[index]))
                matrix[:, index] = np.roll(matrix[:, index], axis=0, shift=roll)
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
