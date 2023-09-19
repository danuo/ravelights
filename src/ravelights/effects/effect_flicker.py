import random

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.effects.effect_super import Effect


class EffectFlicker(Effect):
    def reset(self):
        """
        hue_range controls the color variation for each frame
        """

    def run_before(self):
        ...

    def run_after(self):
        ...

    def render_matrix(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        """Called each render cycle"""
        return in_matrix * random.random()

    def on_delete(self):
        pass
