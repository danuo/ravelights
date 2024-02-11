import numpy as np
from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Vfilter


class VfilterFlippedColorFuse(Vfilter):
    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        flipped_matrix = self.bw_matrix(in_matrix)
        flipped_matrix = np.flip(flipped_matrix, axis=0)
        # todo: improve color handling
        timeline_level = self.device.rendermodule.get_effective_timeline_level()
        sec_color = self.settings.color_engine.get_colors_rgb(timeline_level=timeline_level)[1]
        flipped_matrix = self.colorize_matrix(flipped_matrix, color=sec_color)
        return self.merge_matrices(in_matrix, flipped_matrix)
