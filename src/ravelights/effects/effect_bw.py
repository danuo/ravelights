from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array
from ravelights.effects.effect_super import Effect
from ravelights.vfilters.vfilter_bw import VfilterBW


class EffectBW(Effect):
    def init(self):
        """
        hue_range controls the color variation for each frame
        """

        self.bw_filter = VfilterBW(root=self.root, device=self.device)

    def render_settings_overwrite(self, selected_level: int) -> dict[str, Color]:
        return dict()

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        """Called each render cycle"""
        bw_matrix = self.bw_filter.render(in_matrix=in_matrix, color=color)
        return bw_matrix

    def on_delete(self):
        pass
