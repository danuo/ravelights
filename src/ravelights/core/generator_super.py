import logging
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import numpy as np

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import ArrayFloat
from ravelights.core.timehandler import TimeHandler

if TYPE_CHECKING:
    from ravelights.configs.components import Keywords
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp
    from ravelights.core.settings import Settings

logger = logging.getLogger(__name__)


class Generator(ABC):
    def __init__(
        self,
        root: "RaveLightsApp",
        device: "Device",
        name: str = "undefined",
        keywords: Optional[list["Keywords"]] = None,
        weight: float = 1.0,
        is_prim: bool = True,
        version: int = 0,
        p_add_dimmer: float = 0.5,
        p_add_thinner: float = 0.5,
        **kwargs: Optional[dict[str, str | int | float]],  # typing: ignore
    ):
        self.root = root
        self.settings: "Settings" = self.root.settings
        self.timehandler: "TimeHandler" = self.settings.timehandler
        self.device: "Device" = device
        self.n_devices = len(self.root.devices)
        self.pixelmatrix = self.device.pixelmatrix
        self.n_lights: int = self.pixelmatrix.n_lights
        self.n_leds: int = self.pixelmatrix.n_leds
        self.n: int = self.pixelmatrix.n_leds * self.pixelmatrix.n_lights
        self.name: str = name
        self.keywords: list[str] = [k.value for k in keywords] if keywords else []
        self.weight: float = float(weight)
        self.is_prim: bool = is_prim  # set to true if this is loaded as a primary pattern. Relevant for coloring.
        self.version: int = version
        self.p_add_dimmer: float = p_add_dimmer
        self.p_add_thinner: float = p_add_thinner

        self.kwargs: dict[str, Any] = kwargs  # is this used?
        self.force_trigger_overwrite: bool = False
        if not hasattr(self, "possible_triggers"):
            self.possible_triggers: list[BeatStatePattern] = [BeatStatePattern()]

        self.init()
        self.alternate()
        self.reset()

    @abstractmethod
    def init(self):
        """put custom init code in this function instead of overwriting __init__()"""
        ...

    @abstractmethod
    def alternate(self):
        ...

    @abstractmethod
    def reset(self):
        """this function should cause the pattern to output a black image"""
        ...

    @abstractmethod
    def on_trigger(self):
        """called, when trigger is satisfied"""
        ...

    @abstractmethod
    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        return in_matrix

    def sync_send(self) -> Optional[dict[str, Any]]:
        ...

    def sync_load(self, in_dict: Optional[dict[str, Any]]):
        # after set_kwargs is called
        if not isinstance(in_dict, dict):
            return None
        for key, value in in_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"key {key} does not exist in settings")

    def get_new_trigger(self) -> BeatStatePattern:
        return random.choice(self.possible_triggers)

    def get_float_matrix_rgb(self, fill_value: float = 0.0) -> ArrayFloat:
        """
        shape: (n_leds, n_lights, 3)
        Returns empty 3-channel color matrix in correct size and dtype float.
        """

        matrix = np.full(shape=(self.n_leds, self.n_lights, 3), fill_value=fill_value, dtype=float)
        return matrix

    def get_float_matrix_1d_mono(self, fill_value: float = 0.0) -> ArrayFloat:
        """
        shape: (n_leds * n_lights)
        Returns empty 1-channel monochrome matrix in correct size and dtype float.
        shape is (self.n)
        """

        matrix = np.full(shape=(self.n), fill_value=fill_value, dtype=float)
        return matrix

    def get_float_matrix_2d_mono(self, fill_value: float = 0.0) -> ArrayFloat:
        """
        shape: (self.n_leds, self.n_lights)
        Returns empty 1-channel monochrome matrix in correct size and dtype float.
        shape is (self.n_leds, self.n_lights)
        """

        matrix = np.full(shape=(self.n_leds, self.n_lights), fill_value=fill_value, dtype=float)
        return matrix

    def colorize_matrix(self, matrix_mono: ArrayFloat, color: Color) -> ArrayFloat:
        """
        in:  Nx1
        out: Nx3
        function to colorize a matrix with a given color
        for colorization, another dimension is added
        special case: input matrix is 1d of size n:
        (n) -> (n_leds, n_lights, 3)  /special case
        (x) -> (x,3)
        (x,y) -> (x,y,3)
        """

        # prepare output matrix of correct size
        if matrix_mono.ndim == 1:
            if matrix_mono.shape == (self.n,):
                matrix_mono = matrix_mono.reshape((self.n_leds, self.n_lights), order="F")
                matrix_rgb = np.zeros((self.n_leds, self.n_lights, 3))
            else:
                matrix_rgb = np.zeros((matrix_mono.size, 3))
        elif matrix_mono.ndim == 2:
            matrix_rgb = np.zeros((*matrix_mono.shape, 3))

        shape = [1] * matrix_mono.ndim + [3]
        color_array: ArrayFloat = np.array(color).reshape(shape)
        matrix_rgb = matrix_mono[..., None] * color_array
        return matrix_rgb

    @staticmethod
    def bw_matrix(matrix_rgb: ArrayFloat) -> ArrayFloat:
        """
        in:  Nx3
        out: Nx1
        turns a matrix with shape (..., 3) into a black and white matrix of shape (...)
        """

        return np.amax(matrix_rgb, axis=-1)

    @staticmethod
    def add_matrices(matrix_1: ArrayFloat, matrix_2: ArrayFloat) -> ArrayFloat:
        """Adds two matrices together and caps the brightness (max value) to 1."""
        return np.fmin(1.0, matrix_1 + matrix_2)

    @staticmethod
    def merge_matrices(minor: ArrayFloat, major: ArrayFloat) -> ArrayFloat:
        """
        Combines two matrices similar to add_matrices. Every pixel with brightness > 0 from matrix 2
        will overwrite matrix 1 at that location. This is superior than add_matrices, as different
        colors do not combine to white"""

        matrix_2_max: ArrayFloat = np.max(major, axis=2)
        matrix_2_max_repeated: ArrayFloat = np.repeat(matrix_2_max[..., None], repeats=3, axis=2)
        return np.where(matrix_2_max_repeated > 0, major, minor)

    @staticmethod
    def apply_mask(in_matrix: ArrayFloat, mask: ArrayFloat) -> ArrayFloat:
        """
        Applies a mask 1-channel mask array to a 3-channel color matrix by multiplication.
        in_matrix: Nx3
        mask: Nx1
        out: Nx3
        """
        mask = np.repeat(mask[:, :, None], 3, axis=2)
        return np.multiply(in_matrix, mask)

    def __repr__(self):
        return f"<Generator {self.name}>"

    @classmethod
    def get_identifier(cls) -> str:
        """returns str identifier of generator type, for example 'pattern' for pattern objects"""
        if cls.__bases__[0] is Generator:
            return cls.__name__.lower()
        else:
            return cls.__bases__[0].__name__.lower()


class Pattern(Generator):
    def render(self, colors: list[Color]) -> ArrayFloat:
        ...


class PatternNone(Pattern):
    """Default pattern with blank output"""

    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, colors: list[Color]) -> ArrayFloat:
        return self.get_float_matrix_rgb()


class Vfilter(Generator):
    """Default vfilter with blank output"""

    ...


class VfilterNone(Vfilter):
    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        return in_matrix


class Thinner(Generator):
    """Default thinner with blank output"""

    ...


class ThinnerNone(Thinner):
    """"""

    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        return in_matrix


class Dimmer(Generator):
    """Default dimmer with blank output"""

    ...


class DimmerNone(Dimmer):
    def init(self):
        ...

    def alternate(self):
        ...

    def reset(self):
        ...

    def on_trigger(self):
        ...

    def render(self, in_matrix: ArrayFloat, colors: list[Color]) -> ArrayFloat:
        return in_matrix
