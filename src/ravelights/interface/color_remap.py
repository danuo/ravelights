from enum import Enum
from typing import Callable

from ravelights.core.custom_typing import ArrayFloat

ColorMapping = Callable[[ArrayFloat], ArrayFloat]


def linear_color_mapping(in_matrix: ArrayFloat) -> ArrayFloat:
    print("linear_color_mapping()")
    return in_matrix


def ws2815_color_mapping(in_matrix: ArrayFloat) -> ArrayFloat:
    print("ws2815_color_mapping()")
    return in_matrix


class ColorProfiles(Enum):
    LINEAR: ColorMapping = linear_color_mapping
    WS2815: ColorMapping = ws2815_color_mapping
