import random
from typing import Type

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.generator_super import Pattern
from ravelights.core.utils import p
from ravelights.lights.lights_super import FallingSmallBlock, LightObject, Meteor, Sine, Slideblock, SlideStrobe, SymmetricalStrobe


class PatternStrobeSpawner(Pattern):
    # ! this is WIP
    """pattern name: p_swiper"""

    def init(self):
        self.queues: list[list[LightObject]] = [[] for _ in range(self.n_lights)]

    def alternate(self):
        self.light_selection = random.choice(["all", "half", "random", "random_v2"])

    def reset(self):
        ...

    def on_trigger(self):
        for _ in range(3):
            if p(0.3):
                ran = random.randint(3, 9)
                flashes = [x for _ in range(ran) for x in [True, False]]
                self.queue_element(cls=SlideStrobe, flashes=flashes)

    def render(self, colors: list[Color]):
        # ─── Render Queue ─────────────────────────────────────────────
        matrix = self.pixelmatrix.render_ele_to_matrix_mono(queues=self.queues, colors=colors)
        matrix_rgb = self.colorize_matrix(matrix, color=colors[1])
        return matrix_rgb

    def add_element(self, light_id: int, element: LightObject):
        self.queues[light_id].append(element)

    def queue_element(self, cls: Type[LightObject], **kwargs: int):
        self.lights = self.pixelmatrix.get_lights(self.light_selection)
        for light_id in self.lights:
            ele = cls(self.root, self.device, **kwargs)
            self.add_element(light_id, ele)
