import random

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.generator_super import Pattern
from ravelights.core.utils import p
from ravelights.lights.lights_super import FallingSmallBlock, LightObject, OneThing


class PatternMovingStrobeSlow(Pattern):
    """pattern name: p_moving_strobe"""

    def init(self):
        self.queues: list[list[LightObject]] = [[] for _ in range(self.n_lights)]
        # self.possible_triggers = ["0", "0,2"]
        self.possible_triggers = [
            BeatStatePattern(beats=[0], quarters="A", loop_length=1),
            BeatStatePattern(beats=[0], quarters="AC", loop_length=1),
        ]

    def alternate(self, modes: list[int] = [0, 1, 2, 3, 4]):
        # this function will set all parameters randomly. called after init_custom()
        # ─── LIGHT ALTERNATION ───────────────────────────────────────────
        if 1 in modes:
            light_selection = random.choice(["all", "half", "random", "random_v2"])
            self.kwargs["light_selection"] = light_selection

    def reset(self):
        self.queue_elements_one()

    def on_trigger(self):
        if p(0.5):
            self.queue_elements_one()
        if p(0.2):
            self.queue_elements_two()

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        matrix = self.pixelmatrix.render_ele_to_matrix_mono(queues=self.queues, colors=colors)
        matrix_rgb = self.colorize_matrix(matrix, color=colors[0])
        return matrix_rgb

    def sync_load(self, in_dict: dict):
        # todo: not implemented
        self.lights = self.pixelmatrix.get_lights(self.kwargs["light_selection"])

    def add_element(self, light_id: int, element: LightObject):
        self.queues[light_id].append(element)

    def queue_elements_one(self):
        self.lights = self.pixelmatrix.get_lights(self.kwargs["light_selection"])
        flip = True if p(0.5) else False
        for light_id in self.lights:
            ele = OneThing(self.root, self.device, flip=flip)
            self.add_element(light_id, ele)

    def queue_elements_two(self):
        temp_lights = self.pixelmatrix.get_lights("half")
        flip = True if p(0.5) else False
        for light_id in temp_lights:
            ele = FallingSmallBlock(self.root, self.device, flip=flip)
            self.add_element(light_id, ele)
