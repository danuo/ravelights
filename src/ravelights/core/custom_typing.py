# ruff: noqa: F811
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Protocol, Type, TypedDict

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from ravelights.configs.components import Keywords
    from ravelights.core.device_shared import DeviceLightConfig
    from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
    from ravelights.core.template_objects import EffectSelectorPlacing, GenPlacing, GenSelector
    from ravelights.effects.effect_super import Effect

T_BLUEPRINTS = list["BlueprintGen"] | list["BlueprintEffect"] | list["BlueprintSel"] | list["BlueprintPlace"]

Array = NDArray[Any]
ArrayFloat = NDArray[np.float_]
ArrayInt = NDArray[np.int_]
ArrayUInt8 = NDArray[np.uint8]

DiscoveryUpdateCallback = Callable[[str, str | None], None]


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


class Blueprint(NamedTuple):
    cls: Type["Pattern"] | Type["Vfilter"] | Type["Dimmer"] | Type["Thinner"] | Type["Effect"] | Type[
        "EffectSelectorPlacing"
    ] | Type["GenPlacing"] | Type["GenSelector"]
    args: dict[str, str | float | int | list["Keywords"] | Type["Generator"] | list[int]]


class BlueprintGen(Blueprint):
    ...


class BlueprintEffect(Blueprint):
    ...


class BlueprintSel(Blueprint):
    ...


class BlueprintPlace(Blueprint):
    ...


class BlueprintTimeline(TypedDict):  # todo: move to custom typing
    meta: dict[str, str]
    selectors: list["GenSelector"]
    placements: list["GenPlacing"]
