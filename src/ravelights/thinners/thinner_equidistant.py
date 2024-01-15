import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import Array
from ravelights.core.generator_super import Thinner
from ravelights.core.time_handler import BeatStatePattern


class ThinnerEquidistant(Thinner):
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
        if self.settings.global_thinning_ratio >= 1.0:
            return
        self.mask[:] = 0

        skip_led = list(range(10))
        brightness_fraction = [1.0 / (1 + x) for x in skip_led]

        bright_target = self.settings.global_thinning_ratio
        bright_target = 0.1
        skip_selection = np.argmin([abs(bright - bright_target) for bright in brightness_fraction])
        self.mask[:: skip_led[skip_selection]] = 1

    def render(self, in_matrix: Array, colors: list[Color]) -> Array:
        matrix = self.apply_mask(in_matrix=in_matrix, mask=self.mask.reshape(self.n_leds, -1))
        return matrix
