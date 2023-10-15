import random
from typing import Type

from ravelights.core.colorhandler import Color
from ravelights.core.generator_super import Pattern
from ravelights.core.utils import p
from ravelights.lights.lights_super import LightObject, Meteor


class PatternRandomMeteor(Pattern):
    # ! WIP pattern
    """pattern name: p_random_meteor"""

    def init(self):
        self.queues: list[list[LightObject]] = [[] for _ in range(self.n_lights)]
        light_selection: str = random.choice(["all", "half", "random", "random_v2"])
        self.set_kwargs(light_selection=light_selection)

    def alternate(self):
        self.flip = random.choice([1.0, 0.5, 0.0])

    def on_trigger(self):
        ele = Meteor
        if p(0.9):
            ran = random.randint(3, 9)
            flashes = [x for _ in range(ran) for x in [True, False]]
            self.queue_element(Ele=ele, flip=self.flip)

    def add_element(self, light_id: int, element: LightObject):
        self.queues[light_id].append(element)

    def queue_element(self, Ele: Type[LightObject], **kwargs: int):
        self.lights = self.pixelmatrix.get_lights(self.kwargs["light_selection"])
        for light_id in self.lights:
            ele = Ele(settings=self.settings, pixelmatrix=self.pixelmatrix, **kwargs)
            self.add_element(light_id, ele)

    def render(self, colors: list[Color]):
        matrix = self.pixelmatrix.render_ele_to_matrix_mono(queues=self.queues, colors=colors)
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
