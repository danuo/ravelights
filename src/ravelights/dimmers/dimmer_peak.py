from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Dimmer


class DimmerPeak(Dimmer):
    def init(self, frequency: int = 1):
        self.frequency = frequency

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: list[Color]):
        x = self.timehandler.get_beat_progress_n(self.frequency)
        x_shift = abs((x - 0.5) * 2)
        intensity = max(x_shift**2 * 0.3, x_shift**5)
        matrix = in_matrix * intensity
        return matrix
