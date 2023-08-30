from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayNx3
from ravelights.core.generator_super import Dimmer


class DimmerDecaySlow(Dimmer):
    def init(self):
        self.force_trigger_overwrite = True
        self.possible_triggers = [
            BeatStatePattern(loop_length=2),
            BeatStatePattern(loop_length=4),
            BeatStatePattern(loop_length=8),
            BeatStatePattern(loop_length=16),
        ]
        self.decay_ref = self.timehandler.time_0
        self.trigger = BeatStatePattern(loop_length=4)  # only used to determine decay_factor
        self.decay_factor = 3

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        self.decay_ref = self.timehandler.time_0

    def render(self, in_matrix: ArrayNx3, colors: list[Color]) -> ArrayNx3:
        decay: float = 1 + (self.timehandler.time_0 - self.decay_ref) * self.decay_factor
        matrix: ArrayNx3 = in_matrix * (1 / decay)
        return matrix
