# ruff: noqa: F811
from typing import TYPE_CHECKING, Any, Callable, Optional, Protocol, TypedDict

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from ravelights.core.device_shared import DeviceLightConfig
    from ravelights.core.timeline import GenPlacing, GenSelector


Array = NDArray[Any]
ArrayFloat = NDArray[np.float_]
ArrayInt = NDArray[np.int_]
ArrayUInt8 = NDArray[np.uint8]

DiscoveryUpdateCallback = Callable[[str, Optional[str]], None]


def assert_dims(in_matrix: NDArray[Any], *dims: int):
    """checks if shape is (n_leds, n_lights, 3). this is a debug function"""
    assert in_matrix.shape == dims


class Transmitter(Protocol):
    def _send_bytes(self, data) -> None:
        ...


class LightIdentifier(TypedDict):
    device: int
    light: int
    flip: bool


class TransmitterConfig(TypedDict):
    transmitter: Transmitter
    light_mapping_config: list[list[LightIdentifier]]
    hostname: str


class GeneratorMeta(TypedDict):
    generator_name: str
    generator_keywords: list[str]
    generator_weight: float


class VisualizerConfig(TypedDict):
    name: str
    device_config: list["DeviceLightConfig"]
    visualizer_config: list[list[dict[str, float]]]


class AvailableGenerators(TypedDict):
    pattern: list[GeneratorMeta]
    vfilter: list[GeneratorMeta]
    thinner: list[GeneratorMeta]
    dimmer: list[GeneratorMeta]
    effect: list[GeneratorMeta]


class Timeline(TypedDict):  # todo: move to custom typing
    meta: dict[str, str]
    selectors: list["GenSelector"]
    placements: list["GenPlacing"]
