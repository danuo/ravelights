import random
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat, ArrayUInt8
from ravelights.core.utils import p

if TYPE_CHECKING:
    from ravelights.lights.lights_super import LightObject


class PixelMatrix:
    """Represents the light hardware. After pattern rendering, frames are stored
    in this class. Classes for Artnet or GUI receive frames form here."""

    def __init__(self, n_leds: int, n_lights: int, is_prim: bool):
        self.n_leds: int = n_leds
        self.n_lights: int = n_lights
        self.n = n_leds * n_lights
        self.is_prim: bool = is_prim
        self.reset()

    def reset(self) -> None:
        self.matrix_float: ArrayFloat = np.zeros(shape=(self.n_lights, self.n_leds, 3))

    def set_matrix_float(self, matrix: ArrayFloat):
        """
        matrix with:
        shape: (self.n_leds, self.n_lights, 3)
        value range: [0, 1]
        dtype: float

        """
        assert np.max(matrix) <= 1.0
        assert matrix.shape == (self.n_leds, self.n_lights, 3)
        self.matrix_float = matrix

    def get_matrix_float(self) -> ArrayFloat:
        return self.matrix_float

    def get_matrix_int(self, brightness: float = 1.0) -> ArrayUInt8:
        return (self.matrix_float * 255 * brightness).astype(np.uint8)

    def get_ledid_lightid_from_index(self, index: int):
        """gives led_id and light_id for any index.

        example: if there are lights with 100 pixels each, the
        input:  index=233 will result in the
        output: led_id=2 and light_id 33"""

        # led_id = index % self.n_leds
        # light_id = index // self.n_leds
        # return led_id, light_id
        return divmod(index, self.n_leds)

    @staticmethod
    def clip_matrix_to_1(matrix: ArrayFloat) -> ArrayFloat:
        return np.fmin(1.0, matrix)

    def get_lights(self, light_selection: str = "") -> NDArray[np.int_]:
        if light_selection == "":
            light_selection = random.choice(["half", "random", "random_v2", "full"])
        if light_selection == "half":
            return np.arange(0, self.n_lights, 2) if p(0.5) else np.arange(1, self.n_lights, 2)
        elif light_selection == "random":
            chance = np.random.uniform(0.2, 0.5)
            return np.array([i for i in range(self.n_lights) if p(chance)])
        elif light_selection == "random_v2":
            # get lights
            n_elements = random.choice(range(self.n_lights))
            choices = random.choices(population=range(self.n_lights), k=n_elements)
            return np.array(choices)
        else:  # full
            return np.arange(self.n_lights)

    def render_ele_to_matrix_mono(self, queues: list[list["LightObject"]], colors: list[Color]) -> ArrayFloat:
        """Renders lists of LightObjects (one queue per light) to a blank matrix."""

        matrix = np.zeros(shape=(self.n_leds, self.n_lights))
        for light_id in range(self.n_lights):
            matrix_view = matrix[:, light_id]
            elements_for_deletion: set[LightObject] = set()
            for ele in queues[light_id]:
                ele_matrix, done = ele.render_super(colors)
                if done is True:
                    elements_for_deletion.add(ele)
                else:
                    matrix_view[:] = matrix_view[:] + ele_matrix
            for ele in elements_for_deletion:
                queues[light_id].remove(ele)
        matrix = np.fmin(1, matrix)
        return matrix

    def get_float_matrix_rgb(self, fill_value: float = 0.0) -> ArrayFloat:
        # todo: this is duplicate. move all these functions here
        """
        shape: (n_leds, n_lights, 3)
        Returns empty 3-channel color matrix in correct size and dtype float.
        """

        matrix = np.full(shape=(self.n_leds, self.n_lights, 3), fill_value=fill_value, dtype=float)
        return matrix
