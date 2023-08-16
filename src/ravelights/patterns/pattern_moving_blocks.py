import random
from dataclasses import astuple, dataclass

import numpy as np

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayNx1
from ravelights.core.generator_super import Pattern


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
        version = random.choice([0, 1, 2, 3])
        # version = 0
        if version == 0:
            self.n_states = 50
            self.n_lengths = 10
            self.length_step_factor = 2
            self.n_speed = 20
            self.n_items = 10
            self.brightness = 1.0
        if version == 1:
            self.n_states = 50
            self.n_lengths = 8
            self.length_step_factor = 3
            self.n_speed = 20
            self.n_items = 15
            self.brightness = 1.0
        if version == 2:
            self.n_states = 50
            self.n_lengths = 10
            self.length_step_factor = 4
            self.n_speed = 0  # no speed but reset constantly
            self.n_items = 15
            self.brightness = 1.0
            # self.possible_triggers = ["0", "0,1", "0,2", "1,2,3,4"]
        if version == 3:
            self.n_states = 50
            self.n_lengths = 10
            self.length_step_factor = 4
            self.n_speed = 2
            self.n_items = 15
            self.brightness = 0.5

        # ─── Generate Prerendered Blocks ──────────────────────────────
        def sequence_func(num: int):
            num = int(num)
            while True:
                yield num
                num = int(num + num / self.length_step_factor)

        lengths = [next(sequence_func(4)) for _ in range(self.n_lengths)]
        self.prerendered_matrices: list[ArrayNx1] = []
        for length in lengths:
            matrix = np.zeros(shape=(self.matrix_length))
            a = int(self.matrix_length / 2 - length / 2)
            b = int(self.matrix_length / 2 + length / 2)
            matrix[a:b] = 1.0
            self.prerendered_matrices.append(matrix)

    def reset(self):
        self.states: list[State] = []
        for _ in range(self.n_items):
            item_id = random.randrange(0, len(self.prerendered_matrices))
            bright = random.uniform(0, 1)
            pos = random.uniform(0, self.matrix_length)
            speed = 0 if self.n_speed == 0 else random.uniform(-self.n_speed, self.n_speed)
            self.states.append(State(item_id, bright, pos, speed))

    def on_trigger(self):
        self.reset()

    def render(self, color: Color):
        matrix = self.get_float_matrix_2d_mono()
        for light_id in range(self.n_lights):
            matrix_view = matrix[:, light_id]
            for state in self.states:
                item_id, bright, pos, speed = state
                rolled_view = np.roll(self.prerendered_matrices[item_id], shift=int(pos))
                matrix_view[:] = matrix_view + self.brightness * bright * rolled_view[: self.pixelmatrix.n_leds]
                state.pos = state.pos + speed
        matrix = self.pixelmatrix.clip_matrix_to_1(matrix)
        matrix_rgb = self.colorize_matrix(matrix, color=color)
        return matrix_rgb
