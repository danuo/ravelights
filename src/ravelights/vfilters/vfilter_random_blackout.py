import random

import numpy as np

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayMxKx3
from ravelights.core.generator_super import Vfilter


class VfilterRandomBlackout(Vfilter):
    def init(self):
        self.possible_triggers = [
            BeatStatePattern(loop_length=2, p=0.1),
            BeatStatePattern(loop_length=4, p=0.5),
            BeatStatePattern(loop_length=8),
        ]
        self.on_trigger()

    def alternate(self):
        self.use_devices = random.choice(["all", "one"])

    def sync_send(self):
        return dict(use_devices=self.use_devices)

    def reset(self):
        ...

    def on_trigger(self):
        self.counter_frames = 0
        limit_quarters = random.choice([1, 2, 3, 4, 6, 8])
        self.limit_frames = int(round(limit_quarters * self.settings.beat_time * self.settings.fps))
        self.source_index = None

    def render(self, in_matrix: ArrayMxKx3, colors: list[Color]) -> ArrayMxKx3:
        out_matrix = self.get_float_matrix_rgb()
        if self.use_devices == "all":
            pass
        elif self.use_devices == "one":
            rng = random.Random(self.settings.timehandler.time_0)
            active_device_id = rng.randrange(0, self.n_devices)
            if active_device_id != self.device.device_id:
                return out_matrix

        if self.source_index is None:
            bw_matrix = self.bw_matrix(in_matrix)
            self.source_index = np.argmax(np.mean(bw_matrix, axis=0))
        if self.counter_frames < self.limit_frames:
            out_index = random.randrange(0, self.n_lights)
            out_matrix[:, out_index, :] = in_matrix[:, self.source_index, :]
        self.counter_frames += 1
        return out_matrix
