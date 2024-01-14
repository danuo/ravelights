import random
from typing import TYPE_CHECKING

from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import Array
from ravelights.core.generator_super import Vfilter
from ravelights.effects.effect_super import Effect

if TYPE_CHECKING:
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp


class SpecialEffectVfilter(Effect):
    """
    used to derive one new effect for each vfilter
    do not register in components
    """

    def __init__(self, root: "RaveLightsApp", device: "Device", name: str, vfilter: type["Vfilter"]):
        super().__init__(root, device, name)
        self.vfilter = vfilter(root, device, name)

    def alternate(self):
        self.vfilter.alternate()

    def get_new_trigger(self):
        return random.choice(self.vfilter.possible_triggers)

    def on_trigger(self):
        self.vfilter.on_trigger()

    def reset(self):
        """
        hue_range controls the color variation for each frame
        """

    def run_before(self):
        ...

    def run_after(self):
        ...

    def render_matrix(self, in_matrix: Array, colors: list[Color]) -> Array:
        return self.vfilter.render(in_matrix, colors)

    def on_delete(self):
        ...
