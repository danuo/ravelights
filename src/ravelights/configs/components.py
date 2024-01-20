from enum import auto
from typing import Any, Optional, overload

from ravelights.core.blueprints import BlueprintGenNew
from ravelights.core.custom_typing import (
    BlueprintEffect,
    BlueprintGen,
    BlueprintPlace,
    BlueprintSel,
    BlueprintTimeline,
)
from ravelights.core.generator_super import (
    DimmerNone,
    Generator,
    Pattern,
    PatternNone,
    ThinnerNone,
    Vfilter,
    VfilterNone,
)
from ravelights.core.template_objects import EffectSelectorPlacing, GenPlacing, GenSelector
from ravelights.core.utils import StrEnum
from ravelights.dimmers.dimmer_decay_fast import DimmerDecayFast
from ravelights.dimmers.dimmer_decay_medium import DimmerDecayMedium
from ravelights.dimmers.dimmer_decay_slow import DimmerDecaySlow
from ravelights.dimmers.dimmer_decay_very_fast import DimmerDecayVeryFast
from ravelights.dimmers.dimmer_decay_very_slow import DimmerDecayVerySlow
from ravelights.dimmers.dimmer_peak import DimmerPeak
from ravelights.dimmers.dimmer_random_remove import DimmerRandomRemove
from ravelights.dimmers.dimmer_sideswipe import DimmerSideswipe
from ravelights.dimmers.dimmer_sine import DimmerSine
from ravelights.effects.effect_color_shift import EffectColorShift
from ravelights.effects.effect_color_strobe import EffectColorStrobe
from ravelights.effects.effect_color_strobe_rainbow import EffectColorStrobeRainbow
from ravelights.effects.effect_color_strobe_rainbow_pixel import EffectColorStrobeRainbowPixel
from ravelights.effects.effect_color_swap import EffectColorSwap
from ravelights.effects.effect_colorize import EffectColorize
from ravelights.effects.effect_flicker import EffectFlicker
from ravelights.effects.effect_frameskip import EffectFrameskip
from ravelights.effects.effect_super import Effect
from ravelights.patterns.pattern_audio import PatternAudio
from ravelights.patterns.pattern_debug_bpm_sync import PatternDebugBPMSync
from ravelights.patterns.pattern_debug_gradient import PatternDebugGradient
from ravelights.patterns.pattern_debug_linear_block import PatternDebugLinearBlock
from ravelights.patterns.pattern_debug_solid_color import PatternDebugSolidColor
from ravelights.patterns.pattern_double_strobe import PatternDoubleStrobe
from ravelights.patterns.pattern_gradient import PatternGradient
from ravelights.patterns.pattern_hor_stripes import PatternHorStripes
from ravelights.patterns.pattern_inverse_square import PatternInerseSquare
from ravelights.patterns.pattern_meteor import PatternMeteor
from ravelights.patterns.pattern_moving_blocks import PatternMovingBlocks
from ravelights.patterns.pattern_movingstrobe_fast import PatternMovingStrobeFast
from ravelights.patterns.pattern_movingstrobe_slow import PatternMovingStrobeSlow
from ravelights.patterns.pattern_pid import PatternPID
from ravelights.patterns.pattern_pid_inverse import PatternPIDInverse
from ravelights.patterns.pattern_pid_splash import PatternPidSplash
from ravelights.patterns.pattern_rain import PatternRain
from ravelights.patterns.pattern_random_stripes import PatternRandomStripes
from ravelights.patterns.pattern_shadow import PatternShadow
from ravelights.patterns.pattern_shadow_big import PatternShadowBig
from ravelights.patterns.pattern_sin_overlay import PatternSinOverlay
from ravelights.patterns.pattern_sinwave import PatternSinwave
from ravelights.patterns.pattern_sinwave_squares import PatternSinwaveSquares
from ravelights.patterns.pattern_solid_color import PatternSolidColor
from ravelights.patterns.pattern_strobespawner import PatternStrobeSpawner
from ravelights.patterns.pattern_swiper import PatternSwiper
from ravelights.thinners.thinner_equidistant import ThinnerEquidistant
from ravelights.thinners.thinner_random import ThinnerRandom
from ravelights.thinners.thinner_random_pattern import ThinnerRandomPattern
from ravelights.vfilters.vfilter_all_first import VfilterMapAllFirst
from ravelights.vfilters.vfilter_bw import VfilterBW
from ravelights.vfilters.vfilter_edgedetect import VfilterEdgedetect
from ravelights.vfilters.vfilter_flipped_color_fuse import VfilterFlippedColorFuse
from ravelights.vfilters.vfilter_flipver import VfilterFlipVer
from ravelights.vfilters.vfilter_map_propagate import VfilterMapPropagate
from ravelights.vfilters.vfilter_mirror import VfilterMirrorVer
from ravelights.vfilters.vfilter_mirror_hor import VfilterMirrorHor
from ravelights.vfilters.vfilter_random_blackout import VfilterRandomBlackout
from ravelights.vfilters.vfilter_reverb import VfilterReverb
from ravelights.vfilters.vfilter_rgb_shift import VfilterRgbShift
from ravelights.vfilters.vfilter_roll_overlay import VfilterRollOverlay
from ravelights.vfilters.vfilter_some_first import VfilterMapSomeFirst
from ravelights.vfilters.vfilter_time_delay import VfilterTimeDelay


class Keywords(StrEnum):
    TECHNO = auto()
    DISCO = auto()
    AMBIENT = auto()
    CHORUS = auto()
    BUILDUP = auto()
    BREAK = auto()
    DROP = auto()
    STROBE = auto()
    SHORT = auto()  # patterns that work when showed for one beat only. maybe only use four_beat als blacklist?
    LONG = auto()  # patterns that only work when showed for 4 beats or longer


# ─── Blueprint Section ────────────────────────────────────────────────────────
# fmt: off

K = Keywords

blueprint_generators: list[BlueprintGenNew] = [
    BlueprintGenNew(PatternNone, name="p_none", weight=0),
    BlueprintGenNew(VfilterNone, name="v_none", weight=0),
    BlueprintGenNew(ThinnerNone, name="t_none", weight=0),
    BlueprintGenNew(DimmerNone, name="d_none", weight=0),
    BlueprintGenNew(PatternDebugGradient, name="p_debug_gradient", weight=0),
    BlueprintGenNew(PatternDebugBPMSync, name="p_debug_bpm_sync", weight=0),
    BlueprintGenNew(PatternDebugSolidColor, name="p_debug_solid_color", weight=0),
    BlueprintGenNew(PatternDebugLinearBlock, name="p_debug_linear_block", weight=0),
    BlueprintGenNew(PatternAudio, name="p_audio", weight=0),
    BlueprintGenNew(PatternGradient, name="p_graident", weight=0),
    BlueprintGenNew(PatternRandomStripes, name="p_random_stripes", keywords=[K.SHORT, K.LONG, K.CHORUS, K.BUILDUP, K.DROP], weight=2),
    BlueprintGenNew(PatternSolidColor, name="p_solid_color", keywords=[K.SHORT, K.LONG, K.CHORUS, K.BUILDUP, K.BREAK], weight=0),
    BlueprintGenNew(PatternMeteor, version=0, name="p_meteor_fast05", keywords=[K.SHORT, K.LONG, K.CHORUS], weight=0.2),
    BlueprintGenNew(PatternMeteor, version=1, name="p_meteor_fast10", keywords=[K.LONG, K.CHORUS], weight=0.2),
    BlueprintGenNew(PatternMeteor, version=2, name="p_meteor_fast20", keywords=[K.LONG, K.CHORUS], weight=0.2),
    BlueprintGenNew(PatternMeteor, version=3, name="p_meteor_slow30", keywords=[K.LONG, K.CHORUS], weight=0.2),
    BlueprintGenNew(PatternMovingBlocks, name="p_moving_blocks", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGenNew(PatternSwiper, name="p_swiper", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGenNew(PatternSinwave, name="s_sinwave", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGenNew(PatternSinwaveSquares, name="p_sinwave_square", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGenNew(PatternSinOverlay, name="p_sin_overlay", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGenNew(PatternRain, name="p_rain", keywords=[K.SHORT, K.LONG, K.AMBIENT, K.CHORUS]),
    BlueprintGenNew(PatternInerseSquare, name="p_inverse_square", keywords=[K.SHORT, K.LONG, K.AMBIENT, K.CHORUS]),
    BlueprintGenNew(PatternPID, name="p_pid", keywords=[K.SHORT, K.LONG]),
    BlueprintGenNew(PatternPIDInverse, name="p_pid_inverse", keywords=[K.SHORT, K.LONG]),
    BlueprintGenNew(PatternPidSplash, name="p_pid_splash_WIP", keywords=[K.SHORT, K.LONG]),
    BlueprintGenNew(PatternHorStripes, name="p_hor_stripes", keywords=[K.SHORT, K.LONG]),
    BlueprintGenNew(PatternShadow, name="p_shadow", keywords=[K.SHORT, K.LONG]),
    # BlueprintGenNew(PatternShadowBig, name="p_shadow_big", keywords=[K.SHORT, K.LONG]),  # too
    BlueprintGenNew(PatternDoubleStrobe, name="p_double_strobe", keywords=[K.SHORT, K.LONG, K.STROBE]),
    BlueprintGenNew(PatternMovingStrobeSlow, name="p_moving_strobe_slow", keywords=[K.SHORT, K.LONG, K.CHORUS, K.STROBE]),
    BlueprintGenNew(PatternMovingStrobeFast, name="p_moving_strobe_fast", keywords=[K.SHORT, K.LONG, K.CHORUS, K.STROBE]),
    BlueprintGenNew(PatternStrobeSpawner, name="p_strobe_spawner", keywords=[K.SHORT, K.LONG, K.CHORUS, K.STROBE]),
    BlueprintGenNew(VfilterFlipVer, name="v_flip_ver"),
    BlueprintGenNew(VfilterMirrorVer, name="v_mirror_ver"),
    BlueprintGenNew(VfilterBW, name="v_bw"),
    BlueprintGenNew(VfilterRgbShift, name="v_rgb_shift"),
    BlueprintGenNew(VfilterFlippedColorFuse, name="v_flipped_color_fuse"),
    BlueprintGenNew(VfilterMirrorHor, name="v_mirror_hor"),
    BlueprintGenNew(VfilterMapAllFirst, name="v_map_all_first"),
    BlueprintGenNew(VfilterMapSomeFirst, name="v_map_some_first"),
    BlueprintGenNew(VfilterEdgedetect, name="v_edgedetect_1", version=0),
    BlueprintGenNew(VfilterEdgedetect, name="v_edgedetect_3", version=1),
    BlueprintGenNew(VfilterEdgedetect, name="v_edgedetect_5", version=2),
    BlueprintGenNew(VfilterTimeDelay, name="v_time_delay_random", version=0),
    BlueprintGenNew(VfilterTimeDelay, name="v_time_delay_right", version=1),
    BlueprintGenNew(VfilterTimeDelay, name="v_time_delay_left", version=2),
    BlueprintGenNew(VfilterTimeDelay, name="v_time_delay_double", version=3),
    BlueprintGenNew(VfilterTimeDelay, name="v_time_delay_doubleinv", version=4),
    BlueprintGenNew(VfilterReverb, name="v_reverb"),
    BlueprintGenNew(VfilterRollOverlay, name="v_roll_overlay"),
    BlueprintGenNew(VfilterRandomBlackout, name="v_random_blackout"),
    BlueprintGenNew(VfilterMapPropagate, name="v_map_propagate_random", version=0),
    BlueprintGenNew(VfilterMapPropagate, name="v_map_propagate_left", version=1),
    BlueprintGenNew(VfilterMapPropagate, name="v_map_propagate_right", version=2),
    BlueprintGenNew(VfilterMapPropagate, name="v_map_propagate_mid", version=3),
    BlueprintGenNew(VfilterMapPropagate, name="v_map_propagate_midinv", version=4),
    BlueprintGenNew(ThinnerRandomPattern, name="t_random_pattern"),
    BlueprintGenNew(ThinnerRandom, name="t_random"),
    BlueprintGenNew(ThinnerEquidistant, name="t_equidistant", weight=1),
    BlueprintGenNew(DimmerRandomRemove, name="d_random_remove"),
    BlueprintGenNew(DimmerDecayVeryFast, name="d_decay_veryfast", weight=1),
    BlueprintGenNew(DimmerDecayFast, name="d_decay_fast", weight=1),
    BlueprintGenNew(DimmerDecayMedium, name="d_decay_medium", weight=1),
    BlueprintGenNew(DimmerDecaySlow, name="d_decay_slow", weight=1),
    BlueprintGenNew(DimmerDecayVerySlow, name="d_decay_very_slow", weight=1),
    BlueprintGenNew(DimmerSideswipe, name="d_sideswipe_1", weight=1, version=0),
    BlueprintGenNew(DimmerSideswipe, name="d_sideswipe_2", weight=1, version=1),
    BlueprintGenNew(DimmerSine, name="d_sine", weight=1),
    BlueprintGenNew(DimmerPeak, name="d_peak", weight=1),
]

blueprint_effects: list[BlueprintEffect] = [
    BlueprintEffect(EffectColorStrobe, dict(name="e_color_strobe")),
    BlueprintEffect(EffectColorStrobeRainbow, dict(name="e_color_strobe_rainbow")),
    BlueprintEffect(EffectColorStrobeRainbowPixel, dict(name="e_color_strobe_rainbow_pixel")),
    BlueprintEffect(EffectColorShift, dict(name="e_color_shift")),
    BlueprintEffect(EffectColorSwap, dict(name="e_color_swap")),
    BlueprintEffect(EffectColorize, dict(name="e_colorize")),
    BlueprintEffect(EffectFlicker, dict(name="e_flicker")),
    BlueprintEffect(EffectFrameskip, dict(name="e_frameskip")),
]


# todo: effects need length, patterns do not
blueprint_timelines: list[BlueprintTimeline] = [
    {
        "meta": {
            "name": "just one",
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type="p_audio", level=1)),
        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[0])),
        ],
    },
    {
        "meta": {
            "name": "all 1 level",
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=1)),
        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[16*x for x in range(128//16)])),
        ],
    },
    {
        "meta": {
            "name": "4beat 2level",
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=1)),
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=2)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, level=1, p=0.1)),
        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[16*x for x in range(128//16)])),
            BlueprintPlace(GenPlacing, dict(level=2, timings=[16*x + 12 for x in range(128//16)])),
        ],
    },
    {
        "meta": {
            "name": "2beat 2level fast",
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=1)),
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=2)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, level=1, p=0.1)),
        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[2*4*x for x in range(128//8)])),
            BlueprintPlace(GenPlacing, dict(level=2, timings=[2*4*x + 4 for x in range(128//8)])),
        ],
    },
    {
        "meta": {
            "name": "8beat 2level",
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=1)),
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=2)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, level=1, p=0.2)),
        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[32*x for x in range(128//32)])),
            BlueprintPlace(GenPlacing, dict(level=2, timings=[32*x + 28 for x in range(128//32)])),
        ],
    },
    {
        "meta": {
            "name": "8beat 3level",
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=1)),
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=2)),
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=3)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, level=1, p=0.2)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, level=2, p=0.2)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, level=3, p=0.2)),

        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[32*x for x in range(128//32)])),
            BlueprintPlace(GenPlacing, dict(level=2, timings=[32*x + 28 for x in range(128//32)], trigger_on_change=True)),
            BlueprintPlace(GenPlacing, dict(level=3, timings=[32*x + 30 for x in range(128//32)], trigger_on_change=True)),
        ],
    },
    {
        "meta": {
            "name": "8beat 3level fast switching",
        },
        "selectors": [
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=1)),
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=2)),
            BlueprintSel(GenSelector, dict(gen_type=Pattern, level=3)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, level=1, p=0.2)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, level=2, p=0.2)),
            BlueprintSel(GenSelector, dict(gen_type=Vfilter, level=3, p=0.2)),

        ],
        "placements": [
            BlueprintPlace(GenPlacing, dict(level=1, timings=[8*x for x in range(128//8)])),
            BlueprintPlace(GenPlacing, dict(level=2, timings=[8*x + 2 for x in range(128//8)], trigger_on_change=True)),
            BlueprintPlace(GenPlacing, dict(level=3, timings=[8*x + 4 for x in range(128//8)], trigger_on_change=True)),
        ],
    },
]


@overload
def create_from_blueprint(blueprints: list[BlueprintGenNew], kwargs: Optional[dict[str, Any]]=None) -> list[Generator]: ...

@overload
def create_from_blueprint(blueprints: list[BlueprintEffect], kwargs: Optional[dict[str, Any]]=None) -> list[Effect]: ...

@overload
def create_from_blueprint(blueprints: list[BlueprintSel], kwargs: Optional[dict[str, Any]]=None) -> list[GenSelector]: ...

@overload
def create_from_blueprint(blueprints: list[BlueprintPlace], kwargs: Optional[dict[str, Any]]=None) -> list[GenPlacing | EffectSelectorPlacing]: ...

def create_from_blueprint(blueprints, kwargs: Optional[dict[str, Any]]=None) -> Any:
    if kwargs is None:
        kwargs = dict()
    items = [cls(**args, **kwargs) for cls, args in blueprints]
    return items
