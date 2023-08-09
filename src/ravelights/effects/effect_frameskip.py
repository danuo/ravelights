# todo
import random

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array
from ravelights.effects.effect_super import Effect


class EffectFrameskip(Effect):
    """
    sets frameskip to 2
    """

    def reset(self):
        self.frameskip_new = 2  # todo: alternate

    def run_before(self):
        self.frameskip_before = self.settings.frame_skip
        self.frameskip = self.frameskip_new

    def run_after(self):
        self.frameskip = self.frameskip_before

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        """Called each render cycle"""
        return in_matrix * random.random()

    def on_delete(self):
        pass
