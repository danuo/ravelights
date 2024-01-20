from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, cast

from loguru import logger
from ravelights.core.custom_typing import GeneratorMeta
from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
from ravelights.core.settings import Settings
from ravelights.core.utils import get_random_from_weights, p
from ravelights.effects.effect_super import Effect

if TYPE_CHECKING:
    from ravelights.configs.components import Keywords
    from ravelights.core.pattern_scheduler import PatternScheduler
    from ravelights.core.ravelights_app import RaveLightsApp


def get_names_and_weights(generators: list[str], keywords: Optional[list[str]] = None) -> tuple[list[str], list[float]]:
    """Creates a list of generator names and their weights from the specified generator class.
    Only generators with all the given keywords are chosen."""

    if keywords is None:
        keywords = []
    names: list[str] = []
    weights: list[float | int] = []
    for gen in generators:
        gen_keywords: list[str] = cast(list[str], gen["generator_keywords"])
        all_keywords_in_generator = all([k in gen_keywords for k in keywords])
        if all_keywords_in_generator:
            names.append(gen["generator_name"])
            weights.append(cast(float, gen["generator_weight"]))
    return names, weights


@dataclass
class GeneratorSet:
    pattern_name: Optional[str] = None
    vfilter_name: Optional[str] = None
    dimmer_name: Optional[str] = None
    thinner_name: Optional[str] = None


@dataclass
class GenSelector:
    """
    This class is created for every BlueprintSel object in the components configuration. It contains
    functions to select random generators to be placed in the timeline. Various aspects such as keywords
    and current settings are respected when selecting

    most important are the name attributes
    every attribute that is not None will later be applied to settings.selected:
    pattern_name
    vfilter_name
    dimmer_name
    thinner_name
    """

    gen_type: type[Pattern | Vfilter | Dimmer | Thinner] | str
    name: Optional[str] = None
    keywords: list["Keywords"] = field(default_factory=list)
    level: int = 1
    p: float = 1.0  # if chance is not met, set pattern to p_none (black)
    trigger_on_change: bool = True

    def set_root(self, root: "RaveLightsApp"):
        self.root: "RaveLightsApp" = root
        self.settings: Settings = self.root.settings

    def create_generator_set(self) -> GeneratorSet:
        assert hasattr(self, "root"), "set_root() has not been called yet"

        out = GeneratorSet()

        # ─── Pattern ──────────────────────────────────────────────────
        if self.gen_type is Pattern:
            # set pattern, thinner, dimmer
            if self.name is not None:
                out.pattern_name = self.name
            else:
                out.pattern_name = self.get_random_generator(gen_type=Pattern)
            pattern: Pattern = self.root.devices[0].rendermodule.find_generator(name=out.pattern_name)
            assert isinstance(pattern, Pattern)
            self.set_dimmer_thinner(pattern, out)

        # ─── Vfilter ──────────────────────────────────────────────────
        elif self.gen_type is Vfilter:
            # set vfilter
            if self.name is not None:
                out.vfilter_name = self.name
            else:
                out.vfilter_name = self.get_random_generator(gen_type=Vfilter)

        # ─── Dimmer ───────────────────────────────────────────────────
        elif self.gen_type is Dimmer:
            # set dimmer
            if self.name is not None:
                out.dimmer_name = self.name
            else:
                out.dimmer_name = self.get_random_generator(gen_type=Dimmer)

        return out

    def set_dimmer_thinner(self, pattern: Pattern, out_generator_set: GeneratorSet) -> None:
        # ─── Vfilter ──────────────────────────────────────────────────
        # * not related to pattern, add vfilter purely random

        # ─── Dimmer ───────────────────────────────────────────────────
        if p(pattern.p_add_dimmer) and self.settings.renew_dimmer_from_manual:
            out_generator_set.dimmer_name = self.get_random_generator(gen_type=Dimmer)
        else:
            out_generator_set.dimmer_name = "d_none"

        # ─── Thinner ──────────────────────────────────────────────────
        if p(pattern.p_add_thinner) and self.settings.renew_thinner_from_manual:
            out_generator_set.thinner_name = self.get_random_generator(gen_type=Thinner)
        else:
            out_generator_set.thinner_name = "t_none"

    def get_random_generator(self, gen_type: type[Pattern | Vfilter | Dimmer | Thinner]) -> str:
        generators = self.get_gen_list(gen_type=gen_type)
        if self.settings.music_style:
            keywords = self.keywords + [self.settings.music_style]
        else:
            keywords = self.keywords

        # first try
        names, weights = get_names_and_weights(generators=generators, keywords=keywords)
        if len(names) > 0:
            return get_random_from_weights(names=names, weights=weights)

        # second try without music_style
        logger.warning(f"no generators found with keywords {keywords}")
        names, weights = get_names_and_weights(generators=generators, keywords=self.keywords)
        if len(names) > 0:
            return get_random_from_weights(names=names, weights=weights)

        # third try without keywords
        logger.warning(f"no generators found with keywords {keywords}")
        names, weights = get_names_and_weights(generators=generators)
        if len(names) > 0:
            return get_random_from_weights(names=names, weights=weights)
        logger.warning(f"no generators of type {gen_type} found")

        # backup
        return gen_type.get_identifier()[0] + "_none"

    def get_gen_list(self, gen_type: str | type[Generator] | type[Effect]) -> list[GeneratorMeta]:
        identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        if hasattr(self.root, "metahandler"):
            return self.root.metahandler["available_generators"][identifier]
        else:
            return []


@dataclass
class GenPlacing:
    """places instructions into instruction queue at specific timings, to load specific
    generator levels at that time."""

    level: int  # 1, for action="load", only one level makes sense
    timings: list[int]
    p: float = 1.0
    trigger_on_change: bool = True


@dataclass
class EffectSelectorPlacing:
    patternscheduler: "PatternScheduler"

    effect_name: str = field(init=False)

    # gen_type: type[Effect] = Effect
    name: Optional[str] = None
    keywords: list["Keywords"] = field(default_factory=list)
    length_q: int = 4
    timings: list[int] = field(default_factory=list)
    p: float = 1.0

    def __post_init__(self):
        if self.name is not None:
            self.effect_name = self.name
        else:
            self.effect_name = self.get_random_generator(gen_type=Effect)
        self.settings = self.patternscheduler.settings
        self.effect_length_frames = int(self.timehandler.fps * self.timehandler.quarter_time * self.length_q)

    def get_random_generator(self, gen_type: type[Generator]) -> str:
        generators = self.get_gen_list(gen_type=gen_type)
        if self.settings.music_style:
            keywords = self.keywords + [self.settings.music_style]
        else:
            keywords = self.keywords
        names, weights = get_names_and_weights(generators=generators, keywords=keywords)
        assert len(names) > 0
        gen_name = get_random_from_weights(names=names, weights=weights)
        return gen_name

    def get_gen_list(self, gen_type: str | type[Generator] | type[Effect]) -> list[dict[str, str | list[str] | float]]:
        identifier = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        generators = self.settings.meta["available_generators"][identifier]
        return generators


@dataclass
class GenAlternateObject:
    gen_types: str  # "psvtde"
    level: int  # 1 for action="load", only one level makes sense
    timings: list[int] = field(default_factory=list)
    p: float = 1.0
