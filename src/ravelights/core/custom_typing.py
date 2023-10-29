from typing import TYPE_CHECKING, Any, TypedDict

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from ravelights.configs.components import BlueprintEffect, BlueprintGen, BlueprintPlace, BlueprintSel

T_BLUEPRINTS = list["BlueprintGen"] | list["BlueprintEffect"] | list["BlueprintSel"] | list["BlueprintPlace"]

Array = NDArray[Any]
ArrayFloat = NDArray[np.float_]
ArrayInt = NDArray[np.int_]
ArrayUInt8 = NDArray[np.uint8]


def assert_dims(in_matrix: NDArray[Any], *dims: int):
    """checks if shape is (n_leds, n_lights, 3). this is a debug function"""
    assert in_matrix.shape == dims


class TransmitDict(TypedDict):
    device: int
    light: int
    flip: bool


class DeviceDict(TypedDict):
    n_lights: int
    n_leds: int


class GeneratorMeta(TypedDict):
    generator_name: str
    generator_keywords: list[str]
    generator_weight: float


class AvailableGenerators(TypedDict):
    pattern: list[GeneratorMeta]
    vfilter: list[GeneratorMeta]
    thinner: list[GeneratorMeta]
    dimmer: list[GeneratorMeta]
    effect: list[GeneratorMeta]
