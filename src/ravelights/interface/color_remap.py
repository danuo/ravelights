from enum import StrEnum, auto
from typing import Callable

import numpy as np
from ravelights.core.custom_typing import ArrayFloat

ColorMapping = Callable[[ArrayFloat], ArrayFloat]


def linear_color_mapping(in_matrix: ArrayFloat) -> ArrayFloat:
    # print("linear_color_mapping()")
    return in_matrix


# todo: extend for RGB
# data: led signal [0,255], perceived brightness [0,1]
LUM_DATA_WS2815 = [
    (0, 0.0),
    (1, 0.0),
    (2, 0.0),
    (3, 0.0),
    (4, 0.1),
    (5, 0.2),
    (6, 0.4),
    (7, 0.6),
    (8, 0.7),
    (20, 0.8),
    (230, 1.0),
]
xp, fp = zip(*LUM_DATA_WS2815)


def ws2815_color_mapping(in_matrix: ArrayFloat) -> ArrayFloat:
    # print("ws2815_color_mapping()", in_matrix.shape)
    # shape is (144, 9, 3)
    return np.interp(in_matrix, fp, xp)


class ColorProfiles(StrEnum):
    LINEAR = auto()
    WS2815 = auto()


ColorProfilesFunctions: dict[str, ColorMapping] = {
    ColorProfiles.LINEAR.value: linear_color_mapping,
    ColorProfiles.WS2815.value: ws2815_color_mapping,
}
