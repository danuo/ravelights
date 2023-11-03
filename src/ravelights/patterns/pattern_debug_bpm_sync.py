import random

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern


class PatternDebugBPMSync(Pattern):
    def init(self):
        self.p_add_dimmer = 0.0
        self.p_add_thinner = 0.0
        self.width1 = 5
        self.weidth2 = 5
        self.devices = [0]

    def alternate(self):
        self.devices = random.choices(range(self.n_devices), k=random.randint(1, self.n_devices))

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, colors: list[Color]) -> ArrayFloat:
        # matrix = self.get_float_matrix_rgb()
        matrix = self.get_float_matrix_2d_mono()

        # draw beat_progress

        beat_progress = self.settings.beat_progress
        # beat_progress_adjusted = (0.5 + beat_progress) % 1
        pos = int(round(self.n_leds * beat_progress))
        a = pos - self.width1
        b = pos + self.width1
        a = max(0, a)
        b = min(b, self.n_leds)
        matrix[a:b, :] = 1.0

        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])

        if self.settings.beat_state.is_beat:
            mid = self.n_leds // 2
            matrix_rgb[mid - self.weidth2 : mid + self.weidth2, :] = 1.0

        return matrix_rgb
