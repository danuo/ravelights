import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Dimmer
from ravelights.core.utils import p


class DimmerSideswipe(Dimmer):
    def init(self):
        if self.version == 0:
            self.frequency = 1
        elif self.version == 1:
            self.frequency = 2

    def alternate(self):
        self.flip = p(0.5)

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        progress = self.settings.bpmhandler.get_beat_progress_n(self.frequency)

        mask: ArrayFloat = self.get_float_matrix_2d_mono()
        n = int(progress * self.n_leds)
        mask[n:, :] = 1
        if self.flip:
            mask = np.flip(mask, axis=0)

        matrix = self.apply_mask(in_matrix=in_matrix, mask=mask)
        return matrix
