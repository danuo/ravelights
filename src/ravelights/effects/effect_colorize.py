import numpy as np

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array
from ravelights.effects.effect_super import Effect
from ravelights.vfilters.vfilter_bw import VfilterBW


class EffectColorize(Effect):
    def init(self):
        """
        hue_range controls the color variation for each frame
        """

        self.bw_filter = VfilterBW(root=self.root, device=self.device)  # do not use this

    def render_settings_overwrite(self, selected_level: int) -> dict[str, Color]:
        return dict()

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        # demo color segmentation
        color_matrix = np.zeros(in_matrix.shape[:2])
        color_matrix[:70, :] = 1

        # bw filter
        in_matrix_bw = np.max(in_matrix, axis=-1)

        color_1, color_2, color_effect = self.settings.color_engine.get_colors_rgb(selected_level=1)
        in_matrix_color1 = self.colorize_matrix(in_matrix_bw, color=color_1)
        in_matrix_color2 = self.colorize_matrix(in_matrix_bw, color=color_2)
        out_matrix_rgb = np.where(color_matrix[..., None].repeat(3, axis=2) == 1, in_matrix_color1, in_matrix_color1)
        return out_matrix_rgb

    def on_delete(self):
        pass
