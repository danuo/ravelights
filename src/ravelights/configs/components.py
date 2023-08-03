from enum import Enum
from typing import NamedTuple, Type, overload

from ravelights.core.custom_typing import T_BLUEPRINTS
from ravelights.core.generator_super import Dimmer, DimmerNone, Generator, Pattern, PatternNone, Thinner, ThinnerNone, Vfilter, VfilterNone
from ravelights.core.templateobjects import EffectSelectorPlacing, GenPlacing, GenSelector
from ravelights.dimmers.dimmer_decay_fast import DimmerDecayFast
from ravelights.dimmers.dimmer_decay_medium import DimmerDecayMedium
from ravelights.dimmers.dimmer_decay_slow import DimmerDecaySlow
from ravelights.dimmers.dimmer_decay_very_fast import DimmerDecayVeryFast
from ravelights.dimmers.dimmer_decay_very_slow import DimmerDecayVerySlow
from ravelights.dimmers.dimmer_peak import DimmerPeak
from ravelights.dimmers.dimmer_random_remove import DimmerRandomRemove
from ravelights.dimmers.dimmer_sine import DimmerSine
from ravelights.effects.effect_bw import EffectBW
from ravelights.effects.effect_color_shift import EffectColorShift
from ravelights.effects.effect_color_strobe import EffectColorStrobe
from ravelights.effects.effect_color_strobe_rainbow import EffectColorStrobeRainbow
from ravelights.effects.effect_color_strobe_rainbow_pixel import EffectColorStrobeRainbowPixel
from ravelights.effects.effect_color_swap import EffectColorSwap
from ravelights.effects.effect_colorize import EffectColorize
from ravelights.effects.effect_super import Effect
from ravelights.patterns.pattern_debug import PatternDebug
from ravelights.patterns.pattern_double_strobe import PatternDoubleStrobe
from ravelights.patterns.pattern_meteor import PatternMeteor
from ravelights.patterns.pattern_moving_blocks import PatternMovingBlocks
from ravelights.patterns.pattern_movingstrobe import PatternMovingStrobe
from ravelights.patterns.pattern_movingstrobev2 import PatternMovingStrobeV2
from ravelights.patterns.pattern_pid import PatternPID
from ravelights.patterns.pattern_rain import PatternRain
from ravelights.patterns.pattern_random_stripes import PatternRandomStripes
from ravelights.patterns.pattern_solid_color import PatternSolidColor
from ravelights.patterns.pattern_strobespawner import PatternStrobeSpawner
from ravelights.patterns.pattern_swiper import PatternSwiper
from ravelights.thinners.thinner_equidistant import ThinnerEquidistant
from ravelights.thinners.thinner_random import ThinnerRandom
from ravelights.thinners.thinner_random_pattern import ThinnerRandomPattern
from ravelights.vfilters.vfilter_all_first import VfilterAllFirst
from ravelights.vfilters.vfilter_bw import VfilterBW
from ravelights.vfilters.vfilter_flipver import VfilterFlipVer
from ravelights.vfilters.vfilter_mirror import VfilterMirrorVer
from ravelights.vfilters.vfilter_mirror_hor import VfilterMirrorHor
from ravelights.vfilters.vfilter_some_first import VfilterSomeFirst


class Keywords(Enum):
    TECHNO = "techno"
    DISCO = "disco"
    AMBIENT = "ambient"
    CHORUS = "chorus"
    BUILDUP = "buildup"
    BREAK = "break"
    DROP = "drop"
    STROBE = "strobe"
    ONEBEAT = "one_beat"  # patterns that work when showed for one beat only. maybe only use four_beat als blacklist?
    FOURBEAT = "four_beat"  # patterns that only work when showed for 4 beats or longer


class Blueprint(NamedTuple):
    cls: Type[Generator] | Type[Effect] | Type[EffectSelectorPlacing] | Type[GenPlacing] | Type[GenSelector]
    args: dict[str, str | float | int | list[Keywords] | Type[Generator] | list[int]]


class BlueprintGen(Blueprint):
    ...


class BlueprintEffect(Blueprint):
    ...


class BlueprintSel(Blueprint):
    ...


class BlueprintPlace(Blueprint):
    ...


# pattern DOES NOT NEED need_thinner or need_vfilter tag
# pattern which require this can go to debug category, have pattern with vfilter there
# strobe is not a pattern but rather a special effect that will go away!
# have strobe for techno, disco and ambient?


# ─── Blueprint Section ────────────────────────────────────────────────────────
# flake8: noqa E501
# fmt: off

K = Keywords

blueprint_generators: list[BlueprintGen] = [
    BlueprintGen(PatternNone, dict(name="p_none", weight=0)),
    BlueprintGen(VfilterNone, dict(name="v_none", weight=0)),
    BlueprintGen(ThinnerNone, dict(name="t_none", weight=0)),
    BlueprintGen(DimmerNone, dict(name="d_none", weight=0)),
    BlueprintGen(PatternDebug, dict(name="p_debug", weight=0)),
    BlueprintGen(PatternRandomStripes, dict(name="p_random_stripes", keywords=[K.CHORUS, K.BUILDUP, K.DROP], weight=2)),
    BlueprintGen(PatternSolidColor, dict(name="p_solid_color", keywords=[K.CHORUS, K.BUILDUP, K.BREAK], weight=0)),
    BlueprintGen(PatternMeteor, dict(version=0, name="p_meteor_fast05", keywords=[K.CHORUS], weight=0.2)),
    BlueprintGen(PatternMeteor, dict(version=1, name="p_meteor_fast10", keywords=[K.CHORUS], weight=0.2)),
    BlueprintGen(PatternMeteor, dict(version=2, name="p_meteor_slow30", keywords=[K.CHORUS], weight=0.2)),
    BlueprintGen(PatternMeteor, dict(version=3, name="p_meteor_slow40", keywords=[K.CHORUS], weight=0.2)),
    BlueprintGen(PatternDoubleStrobe, dict(name="p_double_strobe", keywords=[K.STROBE])),
    BlueprintGen(PatternMovingBlocks, dict(name="p_moving_blocks", keywords=[K.CHORUS])),
    BlueprintGen(PatternMovingStrobe, dict(name="p_moving_strobe", keywords=[K.CHORUS, K.STROBE])),
    BlueprintGen(PatternMovingStrobeV2, dict(name="p_moving_strobe_v2", keywords=[K.CHORUS, K.STROBE])),
    BlueprintGen(PatternStrobeSpawner, dict(name="p_strobe_spawner", keywords=[K.CHORUS, K.STROBE])),
    BlueprintGen(PatternSwiper, dict(name="p_swiper", keywords=[K.CHORUS])),
    BlueprintGen(PatternRain, dict(name="p_rain", keywords=[K.AMBIENT, K.CHORUS])),
    BlueprintGen(PatternPID, dict(name="p_pid", keywords=[])),
    BlueprintGen(VfilterFlipVer, dict(name="v_flip_ver")),
    BlueprintGen(VfilterMirrorVer, dict(name="v_mirror_ver")),
    BlueprintGen(VfilterBW, dict(name="v_bw")),
    BlueprintGen(VfilterMirrorHor, dict(name="v_mirror_hor")),
    BlueprintGen(VfilterAllFirst, dict(name="v_all_first")),
    BlueprintGen(VfilterSomeFirst, dict(name="v_some_first")),
    BlueprintGen(ThinnerRandomPattern, dict(name="t_random_pattern")),
    BlueprintGen(ThinnerRandom, dict(name="t_random")),
    BlueprintGen(ThinnerEquidistant, dict(name="t_equidistant", weight=1)),
    BlueprintGen(DimmerRandomRemove, dict(name="d_random_remove")),
    BlueprintGen(DimmerDecayVeryFast, dict(name="d_decay_veryfast", weight=1)),
    BlueprintGen(DimmerDecayFast, dict(name="d_decay_fast", weight=1)),
    BlueprintGen(DimmerDecayMedium, dict(name="d_decay_medium", weight=1)),
    BlueprintGen(DimmerDecaySlow, dict(name="d_decay_slow", weight=1)),
    BlueprintGen(DimmerDecayVerySlow, dict(name="d_decay_very_slow", weight=1)),
    BlueprintGen(DimmerSine, dict(name="d_sine", weight=1)),
    BlueprintGen(DimmerPeak, dict(name="d_peak", weight=1)),
]

blueprint_effects: list[BlueprintEffect] = [
    BlueprintEffect(EffectColorStrobe, dict(name="e_color_strobe")),
    BlueprintEffect(EffectColorStrobeRainbow, dict(name="e_color_strobe_rainbow")),
    BlueprintEffect(EffectColorStrobeRainbowPixel, dict(name="e_color_strobe_rainbow_pixel")),
    BlueprintEffect(EffectColorShift, dict(name="e_color_shift")),
    BlueprintEffect(EffectColorSwap, dict(name="e_color_swap")),
    BlueprintEffect(EffectBW, dict(name="e_bw")),
    BlueprintEffect(EffectColorize, dict(name="e_colorize")),
]

# todo: effects need length, patterns do not
blueprint_timelines: list[dict[str, dict[str, str] | list[BlueprintPlace] | list[BlueprintSel]]] = [
    {  # 0
        "meta": {
            "name": "pattern1",
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=1, name="p_meteor_fast05", p=0.5)),
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=2, keywords=[K.STROBE], trigger="0")),
            # Blueprint(GenSelector, dict(gen_type=Pattern, level=3, element="p_strobe", length=3)),  # todo: implement
        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[16*x for x in range(4)])),  # have this for sure
            # BlueprintPlace(GenPlacing, dict(level=1, timings=[16*4, 20*4, 24*4, 28*4], p=0.1)),  # maybe have this
            BlueprintPlace(GenPlacing, dict(level=2, timings=[0+12, 4*4+12, 8*4+12, 12*4+12, 16*4+12])),  # have this for sure
            BlueprintPlace(GenPlacing, dict(level=2, timings=[16*4+12, 20*4+12, 24*4+12, 28*4+12])),  # have this for sure
            # BlueprintPlace(GenPlacing, dict(level=3, timings=[0])),
            BlueprintPlace(GenPlacing, dict(level=1, timings=[int(128//2)])),
            BlueprintPlace(EffectSelectorPlacing, dict(length_q=8, timings=[0, 32, 64, 96], p=0.9)),
        ],
    },
    {  # 1
       "meta": {
           "name": "simple p1 only",
       },
       "selectors": [
           BlueprintSel(GenSelector, dict(gen_type=Pattern, name="p_solid_color", set_all=False)),
           # BlueprintSel(GenSelector, dict(gen_type=Vfilter, name="v_mirror")),
        #    BlueprintSel(GenSelector, dict(gen_type=Dimmer, name="d_peak")),
       ],
       "placements": [
           BlueprintPlace(GenPlacing, dict(level=1, timings=[0])),
           # BlueprintPlace(EffectSelectorPlacing, dict(length_q=8, timings=[0, 32, 64, 96], p=0.9)),
       ],
    },
    {  # 1
        "meta": {
            "name": "single_pattern",
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, name="p_debug", set_all=False)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, name="v_mirror")),
            # BlueprintSel(GenSelector, dict(gen_type=Dimmer, name="d_sine")),
        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[0])),
            # BlueprintPlace(EffectSelectorPlacing, dict(length_q=8, timings=[0, 32, 64, 96], p=0.9)),
        ],
    },
    {
        "meta": {
            "name": "debug",
            "description": "debug pattern to test filters etc.",
            "weight": 0
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, name="p_debug", set_all=False)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, name="v_mirror")),
            # BlueprintSel(GenSelector, dict(gen_type=Dimmer, name="d_sine")),
        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[0])),
            # BlueprintPlace(EffectSelectorPlacing, dict(length_q=8, timings=[0, 32, 64, 96], p=0.9)),
        ],
    },
    {  # this is a special timeline, it will not be loaded automatically because of weight = 0
        "meta": {
            "name": "special_rainbow_pattern",
            "description": "visualize 1 pattern with permament rainbow effect",
            "weight": 0,
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=1)),
        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[0])),
            BlueprintPlace(EffectSelectorPlacing, dict(name="e_color_strobe", length_q="inf", timings=[0])),  # todo: implement inf timing
        ],
    },
]


@overload
def create_from_blueprint(blueprints: list[BlueprintGen], kwargs) -> list[Generator]: ...

@overload
def create_from_blueprint(blueprints: list[BlueprintEffect], kwargs) -> list[Effect]: ...

@overload
def create_from_blueprint(blueprints: list[BlueprintSel], kwargs) -> list[GenSelector]: ...  # noqa

@overload
def create_from_blueprint(blueprints: list[BlueprintPlace], kwargs) -> list[GenPlacing | EffectSelectorPlacing]: ...  # noqa

def create_from_blueprint(blueprints: T_BLUEPRINTS, kwargs=None):
    if kwargs is None:
        kwargs = dict()
    items = [cls(**args, **kwargs) for cls, args in blueprints]
    return items
