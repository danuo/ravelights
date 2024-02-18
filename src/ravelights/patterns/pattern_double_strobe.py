import random

from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern


class PatternDoubleStrobe(Pattern):
    """pattern name: p_double_strobe"""

    def init(self):
        self.matrix_memory = self.get_float_matrix_1d_mono()

        # ─── PARAMETERS ──────────────────────────────────────────────────
        # tiny blocks
        self.n_blocks = 12
        self.len_min = 2
        self.len_max = 6
        """
        # medium blocks
        self.n_blocks = 8
        self.len_min = 3
        self.len_max = 12
        # big blocks
        self.n_blocks = 4
        self.len_min = 6
        self.len_max = 24
        """

    def alternate(self):
        ...

    def reset(self):
        self.counter = -1

    def on_trigger(self):
        self.counter = -1

    def render(self, colors: tuple[Color, Color]) -> ArrayFloat:
        self.counter += 1
        # ─── GENERATE PATTERN ────────────────────────────────────────────
        if self.counter in [0, 4]:
            self.matrix_memory[:] = 0
            for _ in range(5):
                start_pos = random.randint(0, self.n_lights * self.n_leds - self.len_max)
                length = random.randint(self.len_min, self.len_max)
                self.matrix_memory[start_pos : start_pos + length] = 1.0

        # ─── APPLY PATTERN ON SPECIFIC FRAMES ────────────────────────────
        if self.counter in [0, 2, 4, 6]:
            matrix_rgb = self.colorize_matrix(self.reshape_1d_to_2d(self.matrix_memory), color=colors[0])
            return matrix_rgb
        return self.get_float_matrix_rgb()
