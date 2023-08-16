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
        if self.use_devices == "all":
            self.active_devices = [True] * self.n_devices
        elif self.use_devices == "one":
            self.active_devices = [False] * self.n_devices
            self.active_devices[random.randrange(0, self.n_devices)] = True
        # todo: jump across devices in mode "one"
        # todo: will not be synced in effects right now

    def sync_send(self):
        return dict(active_devices=self.active_devices)

    def reset(self):
        ...

    def on_trigger(self):
        self.counter = 0
        limit_quarters = random.choice([1, 2, 3, 4, 6, 8])
        self.limit_frames = int(round(limit_quarters * self.settings.beat_time * self.settings.fps))
        self.source_index = None

    def render(self, in_matrix: ArrayMxKx3, color: Color) -> ArrayMxKx3:
        print(self.active_devices)
        if self.source_index is None:
            bw_matrix = self.bw_matrix(in_matrix)
            print(bw_matrix.shape)
            self.source_index = np.argmax(np.mean(bw_matrix, axis=0))
            print(self.source_index)
        out_matrix = self.get_float_matrix_rgb()
        if self.active_devices[self.device.device_id] and self.counter < self.limit_frames:
            out_index = random.randrange(0, self.n_lights)
            out_matrix[:, out_index, :] = in_matrix[:, self.source_index, :]
        return out_matrix
