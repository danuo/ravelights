import random
from typing import Any

import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern
from ravelights.core.time_handler import BeatStatePattern
from ravelights.core.utils import p


class PatternMeteor(Pattern):
    """pattern name: p_meteor"""

    def init(self):
        self.p_add_dimmer = 0.0
        self.matrix = self.get_float_matrix_2d_mono()
        self.load_version()

    def load_version(self):
        if self.version == 0:
            self.travel_time = 0.5
            self.width = 30
            self.decay_factor = 0.6
            self.possible_triggers = [
                BeatStatePattern(beats=[0], loop_length=1),
                BeatStatePattern(beats=[0], loop_length=4),
                BeatStatePattern(beats=[0, 1], loop_length=4),
                BeatStatePattern(beats=[0, 2], loop_length=4),
            ]
            self.possible_lengths = [0, 1, 2, 3, 4]  # idea
        if self.version == 1:
            self.travel_time = 1
            self.width = 20
            self.decay_factor = 0.8
            self.possible_triggers = [
                BeatStatePattern(beats=[0], loop_length=1),
                BeatStatePattern(beats=[0], loop_length=2),
                BeatStatePattern(beats=[0], loop_length=2, p=0.4),
                BeatStatePattern(beats=[0], loop_length=4),
                BeatStatePattern(beats=[0, 1], loop_length=4),
                BeatStatePattern(beats=[0, 1], loop_length=8),
            ]
        if self.version == 2:
            self.travel_time = 2
            self.width = 15
            self.decay_factor = 0.9
            self.possible_triggers = [
                BeatStatePattern(beats=[0], loop_length=2),
                BeatStatePattern(beats=[0], loop_length=2, p=0.5),
                BeatStatePattern(beats=[0], loop_length=4),
                BeatStatePattern(beats=[0], loop_length=8),
            ]
        if self.version == 3:
            self.travel_time = 3
            self.width = 10
            self.decay_factor = 0.99
            self.possible_triggers = [
                BeatStatePattern(beats=[0], loop_length=4),
                BeatStatePattern(beats=[0], loop_length=4, p=0.5),
                BeatStatePattern(beats=[0], loop_length=4, p=0.3),
            ]

    def alternate(self, modes: list[int] = [0, 1, 2, 3, 4]):
        # this function will set all parameters randomly. called after init_custom()
        # ─── LIGHT ALTERNATION ───────────────────────────────────────────
        if 1 in modes:
            self.light_selection = random.choice(["all", "half", "random"])
        # ─── FLIP ALTERNATION ────────────────────────────────────────────
        if 2 in modes:
            flip = True if p(0.5) else False
            self.flip = flip
        if 3 in modes:
            mirror = random.choices(
                population=["none", "out_to_in", "in_to_out", "through", "through_magic"],
                weights=[6.0, 1.0, 1.0, 1.0, 1.0],
            )[0]
            self.mirror = mirror
        if 4 in modes:
            flicker = True if p(0.05) else False
            self.flicker = flicker
        self.lights = self.pixelmatrix.get_lights(self.light_selection)

    def sync_send(self):
        """sync will be performed from prim devices to non prim devices"""
        # only export light_selection
        return dict(light_selection=self.light_selection)

    def sync_load(self, in_dict: dict[str, Any]):
        super().sync_load(in_dict=in_dict)
        # todo: fix pixelmatrix light_selection. do i need this?
        self.lights = self.pixelmatrix.get_lights(self.light_selection)

    def reset(self):
        self.matrix[:, :] = 0
        self.n_beats = -1

    def on_trigger(self) -> None:
        if self.light_selection == "random":
            self.lights = self.pixelmatrix.get_lights(self.light_selection)
        # this pattern has to be reset for new meteor
        self.n_beats = -1
        if p(0.2):
            self.alternate()

    def render(self, colors: tuple[Color, Color]) -> ArrayFloat:
        matrix = self.matrix
        # ! cannot execute before reset() is called
        # ─── CALCULATE POSITION FROM BEAT STATE ──────────────────────────
        # pos starting and end position needs to be adjusted, so that it looks 'on beat'
        # duration = 2.5
        # -> 1 | 1 | 0.5
        #    40% | 40 % | 20 %
        # n_beats * 1/2.5 + self.beat_progress / 2.5
        if BeatStatePattern(loop_length=1).is_match(self.timehandler.beat_state):
            self.n_beats += 1
        self.pos = int((self.n_leds - self.width) * (self.n_beats + self.timehandler.beat_progress) / self.travel_time)

        # decay
        decay = np.random.uniform(0.85, 1.0, size=(self.n_leds, self.n_lights)) * self.decay_factor
        decay = np.where(np.random.uniform(0, 1, size=(self.n_leds, self.n_lights)) < 0.05, decay * 0.5, decay)
        matrix[:, :] = matrix * decay

        spawn_chance_np = np.fmax(1.3 - np.abs(self.pos - np.arange(self.n_leds)) / self.width, 0)
        for light_id in self.lights:
            matrix_view = matrix[:, light_id]

            # duplicate
            spawn_chance_np_new = spawn_chance_np.copy()

            # apply mirror_1
            if self.mirror == "out_to_in":
                spawn_chance_np_new[self.n_leds // 2 :] = np.flip(spawn_chance_np_new)[self.n_leds // 2 :]

            if self.mirror == "in_to_out":
                spawn_chance_np_new = np.flip(spawn_chance_np_new)
                spawn_chance_np_new = np.roll(spawn_chance_np_new, -self.n_lights // 2)
                spawn_chance_np_new[self.n_leds // 2 :] = np.flip(spawn_chance_np_new)[self.n_leds // 2 :]

            # apply flip
            if self.mirror == "through_magic":
                if p(0.5):
                    spawn_chance_np_new = np.flip(spawn_chance_np_new)

            # calculate new intensity
            # intensity = np.multiply(np.random.uniform(0, 1), spawn_chance_np_new)  # flicker mode
            intensity: ArrayFloat = np.multiply(np.random.uniform(0, 1, size=self.n_leds), spawn_chance_np_new)
            intensity = np.clip(intensity, 0, 1)

            # add to matrix
            matrix_view[:] = np.fmax(matrix_view, intensity)

            # apply mirror 2
            if self.mirror == "through":
                matrix_view[:] = np.flip(matrix_view)

        self.matrix = matrix

        # ─── PASS MATRIX ─────────────────────────────────────────────────
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
