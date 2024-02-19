# ruff: noqa: F811
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, Protocol, TypedDict

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


LightIndices = tuple[int, ...]
LightSequence = list[LightIndices]


class FramesPattern(NamedTuple):
    length: int
    pattern_indices: tuple[int, ...]


FramesPatternBinary = list[bool]


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


class ToggleSlider(TypedDict):
    type: str
    name_toggle: str
    name_slider: str
    range_min: float
    range_max: float
    step: float
    markers: bool


class Slider(TypedDict):
    type: str
    name_slider: str
    range_min: float
    range_max: float
    step: float
    markers: bool
