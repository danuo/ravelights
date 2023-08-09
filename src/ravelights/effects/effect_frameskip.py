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

    def run_before(self, timeline_level: int):
        # todo
        ...

    def run_after(self, timeline_level: int):
        ...

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        """Called each render cycle"""
        return in_matrix * random.random()

    def on_delete(self):
        pass
