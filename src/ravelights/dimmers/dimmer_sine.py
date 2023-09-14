from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Dimmer
from ravelights.core.utils import cos_mapper


class DimmerSine(Dimmer):
    def init(self, frequency: int = 1):
        self.frequency = frequency

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: list[Color]):
        x = self.settings.bpmhandler.get_beat_progress_n(self.frequency)
        intensity = cos_mapper(x)
        matrix = in_matrix * intensity
        return matrix
