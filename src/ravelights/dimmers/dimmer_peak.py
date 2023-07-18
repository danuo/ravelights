from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayNx3
from ravelights.core.generator_super import Dimmer


class DimmerPeak(Dimmer):
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
        x_shift = abs((x - 0.5) * 2)
        intensity = max(x_shift**2 * 0.3, x_shift**5)
        matrix: ArrayNx3 = in_matrix * intensity
        return matrix
