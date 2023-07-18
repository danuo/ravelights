from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayNx3
from ravelights.core.generator_super import Dimmer
from ravelights.core.utils import cos_mapper


class DimmerSine(Dimmer):
    def init(self, frequency=1):
        self.frequency = frequency

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayNx3, color: Color) -> ArrayNx3:
        x = self.settings.bpmhandler.get_beat_progress_n(self.frequency)
        intensity = cos_mapper(x)
        matrix: ArrayNx3 = in_matrix * intensity
        return matrix
