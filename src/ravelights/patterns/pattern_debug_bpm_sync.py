import random

from ravelights.core.colorhandler import Color
from ravelights.core.generator_super import Pattern


class PatternDebugBPMSync(Pattern):
    def init(self):
        self.p_add_dimmer = 0.0
        self.p_add_thinner = 0.0
        self.width1 = 5
        self.weidth2 = 5
        self.mode = 1

    def alternate(self):
        self.mode = random.choice([1, 2])

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, color: Color):
        matrix = self.get_float_matrix_rgb()

        # draw beat_progress

        beat_progress = self.settings.beat_progress
        # beat_progress_adjusted = (0.5 + beat_progress) % 1
        pos = int(round(self.n_leds * beat_progress))
        a = pos - self.width1
        b = pos + self.width1
        a = max(0, a)
        b = min(b, self.n_leds)
        if self.mode == 1:
            matrix[a:b, :, 0] = 1.0
        else:
            matrix[a:b, 0, 0] = 1.0

        if self.settings.beat_state.is_beat:
            mid = self.n_leds // 2
            if self.mode == 1:
                matrix[mid - self.weidth2 : mid + self.weidth2, :, 1:] = 1.0
            else:
                matrix[mid - self.weidth2 : mid + self.weidth2, 0, 1:] = 1.0

        return matrix
