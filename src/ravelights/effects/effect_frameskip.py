from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.effect_super import Effect


class EffectFrameskip(Effect):
    """
    sets frameskip to 2
    """

    def reset(self):
        self.frameskip_new = 2  # todo: alternate

    def run_before(self):
        self.frameskip_before = self.device.device_settings.device_frameskip
        self.frameskip = self.frameskip_new

    def run_after(self):
        self.device.device_settings.device_frameskip = self.frameskip_before

    def render_matrix(self, in_matrix: ArrayFloat, colors: tuple[Color, Color]) -> ArrayFloat:
        return in_matrix

    def on_delete(self):
        pass
