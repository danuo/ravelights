from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayNx3
from ravelights.core.generator_super import Dimmer


class DimmerDecay(Dimmer):
    def init(self):
        self.force_trigger_overwrite = True
        self.possible_triggers = [
            BeatStatePattern(loop_length=1),
            BeatStatePattern(loop_length=2),
            BeatStatePattern(loop_length=4),
        ]
        self.decay_ref = self.timehandler.time_0
        self.trigger = BeatStatePattern(loop_length=4)  # only used to determine decay_factor

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        self.decay_ref = self.timehandler.time_0

    def render(self, in_matrix: ArrayNx3, color: Color) -> ArrayNx3:
        decay: float = 1 + (self.timehandler.time_0 - self.decay_ref) * self.decay_factor
        matrix: ArrayNx3 = in_matrix * (1 / decay)
        return matrix

    @property
    def decay_factor(self):
        if self.trigger.loop_length >= 4:
            return 0.5
        elif self.trigger.loop_length >= 2:
            return 1
        else:
            return 3
