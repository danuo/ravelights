import random
from typing import Type

from ravelights.core.color_handler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern
from ravelights.core.time_handler import BeatStatePattern
from ravelights.core.utils import p
from ravelights.dimmers.dimmer_sine import DimmerSine
from ravelights.lights.lights_super import (
    FallingSmallBlock,
    LightObject,
    Meteor,
    Sine,
    Slideblock,
    SlideStrobe,
    SymmetricalStrobe,
)


class PatternSwiper(Pattern):
    """pattern name: p_swiper"""

    def init(self):
        # ! careful. must have this trigger!
        self.force_trigger_overwrite = True
        self.possible_triggers = [BeatStatePattern(beats=[0], quarters="C", loop_length=1)]
        self.queues: list[list[LightObject]] = [[] for _ in range(self.n_lights)]
        self.dimmer = DimmerSine(root=self.root, device=self.device, frequency=1)

    def alternate(self):
        self.kwargs["light_selection"] = random.choice(["all", "half", "random", "random_v2"])
        self.p_flip = random.choice([1.0, 0.5, 0.0])

    def reset(self):
        ...

    def on_trigger(self):
        if p(0.9):
            self.queue_element(cls=Meteor, p_flip=self.p_flip)

    def add_element(self, light_id: int, element: LightObject):
        self.queues[light_id].append(element)

    def queue_one(self):
        pass
        # kwargs = dict(flip = True if p(0.5) else False)
        # self.queue_element(cls=OneThing, kwargs=kwargs)

    def queue_element(self, cls: Type[LightObject], **kwargs: int):
        self.lights = self.pixelmatrix.get_lights(self.kwargs["light_selection"])
        for light_id in self.lights:
            flip = p(kwargs["p_flip"])
            ele = cls(self.root, self.device, flip=flip)
            self.add_element(light_id, ele)

    def render(self, colors: tuple[Color, Color]) -> ArrayFloat:
        matrix = self.pixelmatrix.render_ele_to_matrix_mono(queues=self.queues, colors=colors)
        matrix = self.dimmer.render(matrix, colors=colors)
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
