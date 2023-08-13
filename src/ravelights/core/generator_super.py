import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

import numpy as np

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import Color
from ravelights.core.custom_typing import Array, ArrayNx1, ArrayNx3
from ravelights.core.pixelmatrix import PixelMatrix
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
        weight=1.0,
        is_prim: bool = True,
        version: int = 0,
        p_add_dimmer: float = 0.5,
        p_add_thinner: float = 0.5,
        **kwargs: Optional[dict[str, str | int | float]],  # typing: ignore
    ):
        self.root = root
        self.settings: "Settings" = self.root.settings
        self.timehandler: "TimeHandler" = self.settings.timehandler
        self.device = device
        self.init_pixelmatrix(self.device.pixelmatrix)
        self.name = name
        self.keywords: list[str] = [k.value for k in keywords] if keywords else []
        self.weight = weight
        self.is_prim = is_prim  # set to true if this is loaded as a primary pattern. Relevant for coloring.
        self.version = version
        self.p_add_dimmer = p_add_dimmer
        self.p_add_thinner = p_add_thinner

        self.kwargs = kwargs
        self.force_trigger_overwrite = False
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
    def render(self, in_matrix: Array, color: Color) -> Array:
        return in_matrix

    def sync_send(self) -> dict:
        ...

    def sync_load(self, in_dict: dict):
        # after set_kwargs is called
        ...

    def init_pixelmatrix(self, pixelmatrix: "PixelMatrix"):
        self.pixelmatrix = pixelmatrix
        self.n_lights: int = pixelmatrix.n_lights
        self.n_leds: int = pixelmatrix.n_leds
        self.n: int = pixelmatrix.n_leds * pixelmatrix.n_lights

    def get_float_matrix_rgb(self, fill_value: float = 0.0) -> ArrayNx3:
        """
        shape: (n_leds, n_lights, 3)
        Returns empty 3-channel color matrix in correct size and dtype float.
        """

        matrix = np.full(shape=(self.n_leds, self.n_lights, 3), fill_value=fill_value, dtype=float)
        return matrix

    def get_float_matrix_1d_mono(self, fill_value: float = 0.0) -> ArrayNx1:
        """
        shape: (n_leds * n_lights)
        Returns empty 1-channel monochrome matrix in correct size and dtype float.
        shape is (self.n)
        """

        matrix = np.full(shape=(self.n), fill_value=fill_value, dtype=float)
        return matrix

    def get_float_matrix_2d_mono(self, fill_value: float = 0.0) -> ArrayNx1:
        """
        shape: (self.n_leds, self.n_lights)
        Returns empty 1-channel monochrome matrix in correct size and dtype float.
        shape is (self.n_leds, self.n_lights)
        """

        matrix = np.full(shape=(self.n_leds, self.n_lights), fill_value=fill_value, dtype=float)
        return matrix

    def colorize_matrix(self, matrix_mono: ArrayNx1, color: Color) -> ArrayNx3:
        """
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
        color = np.array(color).reshape(shape)
        matrix_rgb = matrix_mono[..., None] * color
        return matrix_rgb

    @staticmethod
    def bw_matrix(matrix_rgb: ArrayNx3) -> ArrayNx1:
        """
        turns a matrix with shape (..., 3) into a black and white matrix of shape (...)
        """

        return np.amax(matrix_rgb, axis=-1)

    @staticmethod
    def add_matrices(matrix_1: Array, matrix_2: Array) -> Array:
        """Adds two matrices together and caps the brightness (max value) to 1."""
        return np.fmin(1.0, matrix_1 + matrix_2)

    @staticmethod
    def merge_matrices(matrix_1: Array, matrix_2: Array) -> Array:
        """
        Combines two matrices similar to add_matrices. Every pixel with brightness > 0 from matrix 2
        will overwrite matrix 1 at that location. This is superior than add_matrices, as different
        colors do not combine to white"""

        matrix_2_max = np.max(matrix_2, axis=2)
        matrix_2_max_repeated = np.repeat(matrix_2_max[..., None], repeats=3, axis=2)
        return np.where(matrix_2_max_repeated > 0, matrix_2, matrix_1)

    @staticmethod
    def apply_mask(in_matrix: ArrayNx3, mask: ArrayNx1) -> ArrayNx3:
        """Applies a mask 1-channel mask array to a 3-channel color matrix by multiplication."""
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
    def render(self, color: Color) -> ArrayNx3:
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

    def render(self, color: Color) -> ArrayNx3:
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

    def render(self, in_matrix: Array, color: Color) -> Array:
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

    def render(self, in_matrix: Array, color: Color) -> Array:
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

    def render(self, in_matrix: Array, color: Color) -> Array:
        return in_matrix
