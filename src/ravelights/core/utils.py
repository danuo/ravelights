import math
import random
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Sequence, Type, TypeVar

import numpy as np
import numpy.typing as npt
from loguru import logger  # type:ignore

if TYPE_CHECKING:
    from ravelights.core.colorhandler import Color

T = TypeVar("T")
_S = TypeVar("_S", bound="StrEnum")


class StrEnum(str, Enum):
    """
    Enum where members are also (and must be) strings
    """

    def __new__(cls: Type[_S], *values: str) -> _S:
        value = str(*values)
        member = str.__new__(cls, value)
        member._value_ = value
        return member

    __str__ = str.__str__  # type: ignore

    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> str:
        """
        Return the lower-cased version of the member name.
        """
        return name.lower()


def p(chance: float) -> bool:
    return random.random() < chance


def get_random_from_weights(names: list[T], weights: list[float]) -> Optional[T]:
    """Return a random item from the list with respect to the weights"""
    if not len(names) > 0:
        logger.warning("called get_random_from_weights() with empty list")
        return None
    random_generator = random.choices(names, weights)[0]
    return random_generator


def i_to_rgb(matrix: npt.NDArray[np.int_ | np.float_], color: "Color") -> npt.NDArray[np.int_ | np.float_]:
    assert matrix.dtype == int
    # matrix [n*1] with 0-1 float value
    # or
    # matrix [n*1] with 0-255 int value
    # Color with 0-1 float value
    n = len(matrix)
    out = np.zeros((n, 3), dtype=matrix.dtype)
    for channel in range(3):
        for pixel in range(n):
            out[pixel, channel] = matrix[pixel] * color[channel]
    return out


def sign(number: float | int) -> float:
    """returns a number with magnitude 1 and sign of number"""
    return math.copysign(1.0, number)


def split_outputs(data_in: Sequence[int | float], len_segment: int) -> list[Sequence[int | float]]:
    outputs: list[Sequence[int | float]] = []
    n_data = len(data_in)
    n_segments: int = n_data // len_segment + 1
    for i in range(n_segments):
        if i == n_segments - 1:
            # last output
            data_segment = data_in[i * len_segment :]
        else:
            data_segment = data_in[i * len_segment : (i + 1) * len_segment]
        outputs.append(data_segment)
    return outputs


def sin_mapper(x: float, out_lower: float = 0.0, out_upper: float = 1.0) -> float:  # , in_lower=0, in_upper=1):
    """
    in:    0 | 1/4   | 2/4   | 3/4   | 4/4
    x:     0 | 1/2pi | 2/2pi | 3/2pi | 4/2pi
    out/y  0 | 1     | 0     | -1    | 0
    """
    sin_value: float = math.sin(x * 2 * math.pi)
    out_value: float = out_lower + (sin_value + 1) * 0.5 * (out_upper - out_lower)
    return out_value


def cos_mapper(x: float, out_lower: float = 0.0, out_upper: float = 1.0) -> float:  # , in_lower=0, in_upper=1):
    """
    in:    0 | 1/4   | 2/4   | 3/4   | 4/4
    x:     0 | 1/2pi | 2/2pi | 3/2pi | 4/2pi
    out/y  1 | 0     | -1     | 0    | 1
    """
    cos_value: float = math.cos(x * 2 * math.pi)
    out_value: float = out_lower + (cos_value + 1) * 0.5 * (out_upper - out_lower)
    return out_value


T_NUM = float | int


def map_value(x: T_NUM, out_range: tuple[T_NUM, T_NUM], in_range: tuple[T_NUM, T_NUM] = (0, 1)) -> float:
    """maps x to the range (A,B), with x being in the range (a,b)

    in_range : (a, b)
    out_range : (A, B)"""

    a, b = in_range
    A, B = out_range
    assert b > a
    assert B > A
    if not a <= x <= b:
        logger.warning("x is not in the range (a,b)")
    ran = b - a
    Ran = B - A
    X = (x - a) / ran
    return A + X * Ran


def lerp(t: float, a: float, b: float) -> float:
    return (1.0 - t) * a + b * t


def invlerp(v: float, a: float, b: float) -> float:
    return (v - a) / (b - a)


def remap(v: float, o_min: float, o_max: float, i_min: float = 0.0, i_max: float = 1.0):
    t = invlerp(v, i_min, i_max)
    return lerp(t, o_min, o_max)
