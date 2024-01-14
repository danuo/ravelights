import random
from typing import Any, Type

from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern
from ravelights.core.timehandler import BeatStatePattern
from ravelights.core.utils import p
from ravelights.lights.lights_super import FallingSmallBlock, LightObject


class PatternRain(Pattern):
    """pattern name: p_rain"""

    def init(self):
        self.queues: list[list[LightObject]] = [[] for _ in range(self.n_lights)]
        self.possible_triggers: list[BeatStatePattern] = [BeatStatePattern(loop_length=1)]
        self.lightcls = FallingSmallBlock

    def alternate(self):
        self.kwargs["light_selection"] = random.choice(["all", "half", "random", "random_v2"])

    def reset(self):
        ...

    def on_trigger(self):
        for _ in range(3):
            if p(0.3):
                ran = random.randint(3, 9)
                flashes: list[bool] = [x for _ in range(ran) for x in [True, False]]
                self.queue_element(cls=self.lightcls, flashes=flashes)

    def add_element(self, light_id: int, element: LightObject):
        self.queues[light_id].append(element)

    def queue_element(self, cls: Type[LightObject], **kwargs: dict[str, Any]):
        self.lights = self.pixelmatrix.get_lights(self.kwargs["light_selection"])
        for light_id in self.lights:
            ele = cls(self.root, self.device, **kwargs)
            self.add_element(light_id, ele)

    def render(self, colors: list[Color]) -> ArrayFloat:
        matrix = self.pixelmatrix.render_ele_to_matrix_mono(queues=self.queues, colors=colors)
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb
