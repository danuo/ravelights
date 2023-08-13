from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayMxKx3
from ravelights.effects.effect_super import Effect


class EffectFrameskip(Effect):
    """
    sets frameskip to 2
    """

    def reset(self):
        self.frameskip_new = 2  # todo: alternate

    def run_before(self):
        self.frameskip_before = self.device.device_frame_skip
        self.frameskip = self.frameskip_new

    def run_after(self):
        self.device.device_frame_skip = self.frameskip_before

    def render_matrix(self, in_matrix: ArrayMxKx3, color: Color) -> ArrayMxKx3:
        return in_matrix

    def on_delete(self):
        pass
