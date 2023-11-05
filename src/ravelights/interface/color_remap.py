from enum import StrEnum, auto
from typing import Callable

from ravelights.core.custom_typing import ArrayFloat

ColorMapping = Callable[[ArrayFloat], ArrayFloat]


def linear_color_mapping(in_matrix: ArrayFloat) -> ArrayFloat:
    print("linear_color_mapping()")
    return in_matrix


def ws2815_color_mapping(in_matrix: ArrayFloat) -> ArrayFloat:
    print("ws2815_color_mapping()")
    return in_matrix


class ColorProfiles(StrEnum):
    LINEAR = auto()
    WS2815 = auto()


ColorProfilesFunctions: dict[str, ColorMapping] = {
    ColorProfiles.LINEAR.value: linear_color_mapping,
    ColorProfiles.WS2815.value: ws2815_color_mapping,
}
