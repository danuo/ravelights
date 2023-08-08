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

    def render_settings_overwrite(self, timeline_level: int) -> dict[str, Color]:
        return dict()

    def render_matrix(self, in_matrix: Array, color: Color) -> Array:
        """Called each render cycle"""
        return in_matrix * random.random()

    def on_delete(self):
        pass
