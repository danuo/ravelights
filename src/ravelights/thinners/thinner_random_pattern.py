import random

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array
from ravelights.core.generator_super import Thinner


class ThinnerRandomPattern(Thinner):
    def init(self):
        self.possible_triggers = [
            BeatStatePattern(beats=[0], quarters="ABCD", loop_length=1),
            BeatStatePattern(beats=[0], quarters="A", loop_length=1),
            BeatStatePattern(beats=[0], quarters="A", loop_length=4),
            BeatStatePattern(beats=[0, 1], quarters="A", loop_length=4),
            BeatStatePattern(beats=[0, 2], quarters="A", loop_length=4),
        ]
        self.mask = self.get_float_matrix_1d_mono(fill_value=1)

    def alternate(self):
        ...

    def reset(self):
        self.on_trigger()

    def on_trigger(self):
        self.mask[:] = 1
        pattern_length = 3
        if self.settings.global_thinning_ratio >= 1.0:
            return
        n = pattern_length * 10 - int(pattern_length * self.settings.global_thinning_ratio)
        assert 0 < n < pattern_length * 10
        items = random.choices(range(pattern_length * 10), k=n)
        for i in items:
            self.mask[i :: pattern_length * 10] = 0

    def render(self, in_matrix: Array, color: Color):
        matrix = self.apply_mask(in_matrix=in_matrix, mask=self.mask.reshape(self.n_leds, -1))
        return matrix
