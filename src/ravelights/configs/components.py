from enum import auto

from ravelights.core.blueprints import BlueprintEffect, BlueprintGen
from ravelights.core.custom_typing import Timeline
from ravelights.core.generator_super import (
    DimmerNone,
    Pattern,
    PatternNone,
    ThinnerNone,
    Vfilter,
    VfilterNone,
)
from ravelights.core.timeline import GenPlacing, GenSelector
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

blueprint_generators: list[BlueprintGen] = [
    BlueprintGen(PatternNone, name="p_none", weight=0),
    BlueprintGen(VfilterNone, name="v_none", weight=0),
    BlueprintGen(ThinnerNone, name="t_none", weight=0),
    BlueprintGen(DimmerNone, name="d_none", weight=0),
    BlueprintGen(PatternDebugGradient, name="p_debug_gradient", weight=0),
    BlueprintGen(PatternDebugBPMSync, name="p_debug_bpm_sync", weight=0),
    BlueprintGen(PatternDebugSolidColor, name="p_debug_solid_color", weight=0),
    BlueprintGen(PatternDebugLinearBlock, name="p_debug_linear_block", weight=0),
    BlueprintGen(PatternAudio, name="p_audio", weight=0),
    BlueprintGen(PatternGradient, name="p_graident", weight=0),
    BlueprintGen(PatternRandomStripes, name="p_random_stripes", keywords=[K.SHORT, K.LONG, K.CHORUS, K.BUILDUP, K.DROP], weight=2),
    BlueprintGen(PatternSolidColor, name="p_solid_color", keywords=[K.SHORT, K.LONG, K.CHORUS, K.BUILDUP, K.BREAK], weight=0),
    BlueprintGen(PatternMeteor, version=0, name="p_meteor_fast05", keywords=[K.SHORT, K.LONG, K.CHORUS], weight=0.2),
    BlueprintGen(PatternMeteor, version=1, name="p_meteor_fast10", keywords=[K.LONG, K.CHORUS], weight=0.2),
    BlueprintGen(PatternMeteor, version=2, name="p_meteor_fast20", keywords=[K.LONG, K.CHORUS], weight=0.2),
    BlueprintGen(PatternMeteor, version=3, name="p_meteor_slow30", keywords=[K.LONG, K.CHORUS], weight=0.2),
    BlueprintGen(PatternMovingBlocks, name="p_moving_blocks", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGen(PatternSwiper, name="p_swiper", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGen(PatternSinwave, name="s_sinwave", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGen(PatternSinwaveSquares, name="p_sinwave_square", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGen(PatternSinOverlay, name="p_sin_overlay", keywords=[K.SHORT, K.LONG, K.CHORUS]),
    BlueprintGen(PatternRain, name="p_rain", keywords=[K.SHORT, K.LONG, K.AMBIENT, K.CHORUS]),
    BlueprintGen(PatternInerseSquare, name="p_inverse_square", keywords=[K.SHORT, K.LONG, K.AMBIENT, K.CHORUS]),
    BlueprintGen(PatternPID, name="p_pid", keywords=[K.SHORT, K.LONG]),
    BlueprintGen(PatternPIDInverse, name="p_pid_inverse", keywords=[K.SHORT, K.LONG]),
    BlueprintGen(PatternPidSplash, name="p_pid_splash_WIP", keywords=[K.SHORT, K.LONG]),
    BlueprintGen(PatternHorStripes, name="p_hor_stripes", keywords=[K.SHORT, K.LONG]),
    BlueprintGen(PatternShadow, name="p_shadow", keywords=[K.SHORT, K.LONG]),
    BlueprintGen(PatternShadowBig, name="p_shadow_big", keywords=[K.SHORT, K.LONG]),
    BlueprintGen(PatternDoubleStrobe, name="p_double_strobe", keywords=[K.SHORT, K.LONG, K.STROBE]),
    BlueprintGen(PatternMovingStrobeSlow, name="p_moving_strobe_slow", keywords=[K.SHORT, K.LONG, K.CHORUS, K.STROBE]),
    BlueprintGen(PatternMovingStrobeFast, name="p_moving_strobe_fast", keywords=[K.SHORT, K.LONG, K.CHORUS, K.STROBE]),
    BlueprintGen(PatternStrobeSpawner, name="p_strobe_spawner", keywords=[K.SHORT, K.LONG, K.CHORUS, K.STROBE]),
    BlueprintGen(VfilterFlipVer, name="v_flip_ver"),
    BlueprintGen(VfilterMirrorVer, name="v_mirror_ver"),
    BlueprintGen(VfilterBW, name="v_bw"),
    BlueprintGen(VfilterRgbShift, name="v_rgb_shift"),
    BlueprintGen(VfilterFlippedColorFuse, name="v_flipped_color_fuse"),
    BlueprintGen(VfilterMirrorHor, name="v_mirror_hor"),
    BlueprintGen(VfilterMapAllFirst, name="v_map_all_first"),
    BlueprintGen(VfilterMapSomeFirst, name="v_map_some_first"),
    BlueprintGen(VfilterEdgedetect, name="v_edgedetect_1", version=0),
    BlueprintGen(VfilterEdgedetect, name="v_edgedetect_3", version=1),
    BlueprintGen(VfilterEdgedetect, name="v_edgedetect_5", version=2),
    BlueprintGen(VfilterTimeDelay, name="v_time_delay_random", version=0),
    BlueprintGen(VfilterTimeDelay, name="v_time_delay_right", version=1),
    BlueprintGen(VfilterTimeDelay, name="v_time_delay_left", version=2),
    BlueprintGen(VfilterTimeDelay, name="v_time_delay_double", version=3),
    BlueprintGen(VfilterTimeDelay, name="v_time_delay_doubleinv", version=4),
    BlueprintGen(VfilterReverb, name="v_reverb"),
    BlueprintGen(VfilterRollOverlay, name="v_roll_overlay"),
    BlueprintGen(VfilterRandomBlackout, name="v_random_blackout"),
    BlueprintGen(VfilterMapPropagate, name="v_map_propagate_random", version=0),
    BlueprintGen(VfilterMapPropagate, name="v_map_propagate_left", version=1),
    BlueprintGen(VfilterMapPropagate, name="v_map_propagate_right", version=2),
    BlueprintGen(VfilterMapPropagate, name="v_map_propagate_mid", version=3),
    BlueprintGen(VfilterMapPropagate, name="v_map_propagate_midinv", version=4),
    BlueprintGen(ThinnerRandomPattern, name="t_random_pattern"),
    BlueprintGen(ThinnerRandom, name="t_random"),
    BlueprintGen(ThinnerEquidistant, name="t_equidistant", weight=1),
    BlueprintGen(DimmerRandomRemove, name="d_random_remove"),
    BlueprintGen(DimmerDecayVeryFast, name="d_decay_veryfast", weight=1),
    BlueprintGen(DimmerDecayFast, name="d_decay_fast", weight=1),
    BlueprintGen(DimmerDecayMedium, name="d_decay_medium", weight=1),
    BlueprintGen(DimmerDecaySlow, name="d_decay_slow", weight=1),
    BlueprintGen(DimmerDecayVerySlow, name="d_decay_very_slow", weight=1),
    BlueprintGen(DimmerSideswipe, name="d_sideswipe_1", weight=1, version=0),
    BlueprintGen(DimmerSideswipe, name="d_sideswipe_2", weight=1, version=1),
    BlueprintGen(DimmerSine, name="d_sine", weight=1),
    BlueprintGen(DimmerPeak, name="d_peak", weight=1),
]

blueprint_effects: list[BlueprintEffect] = [
    BlueprintEffect(EffectColorStrobe, name="e_color_strobe"),
    BlueprintEffect(EffectColorStrobeRainbow, name="e_color_strobe_rainbow"),
    BlueprintEffect(EffectColorStrobeRainbowPixel, name="e_color_strobe_rainbow_pixel"),
    BlueprintEffect(EffectColorShift, name="e_color_shift"),
    BlueprintEffect(EffectColorSwap, name="e_color_swap"),
    BlueprintEffect(EffectColorize, name="e_colorize"),
    BlueprintEffect(EffectFlicker, name="e_flicker"),
    BlueprintEffect(EffectFrameskip, name="e_frameskip"),
]

# todo: effects need length, patterns do not
blueprint_timelines: list[Timeline] = [
    {
        "meta": {
            "name": "just one",
        },
        "selectors": [
            GenSelector(gen_type="p_audio", level=1),
        ],
        "placements": [
            GenPlacing(level=1, timings=[0]),
        ],
    },
    {
        "meta": {
            "name": "all 1 level",
        },
        "selectors": [
            GenSelector(gen_type=Pattern, level=1),
        ],
        "placements": [
            GenPlacing(level=1, timings=[16*x for x in range(128//16)]),
        ],
    },
    {
        "meta": {
            "name": "4beat 2level",
        },
        "selectors": [
            GenSelector(gen_type=Pattern, level=1),
            GenSelector(gen_type=Pattern, level=2),
            GenSelector(gen_type=Vfilter, level=1, p=0.1),
        ],
        "placements": [
            GenPlacing(level=1, timings=[16*x for x in range(128//16)]),
            GenPlacing(level=2, timings=[16*x + 12 for x in range(128//16)]),
        ],
    },
    {
        "meta": {
            "name": "2beat 2level fast",
        },
        "selectors": [
            GenSelector(gen_type=Pattern, level=1),
            GenSelector(gen_type=Pattern, level=2),
            GenSelector(gen_type=Vfilter, level=1, p=0.1),
        ],
        "placements": [
            GenPlacing(level=1, timings=[2*4*x for x in range(128//8)]),
            GenPlacing(level=2, timings=[2*4*x + 4 for x in range(128//8)]),
        ],
    },
    {
        "meta": {
            "name": "8beat 2level",
        },
        "selectors": [
            GenSelector(gen_type=Pattern, level=1),
            GenSelector(gen_type=Pattern, level=2),
            GenSelector(gen_type=Vfilter, level=1, p=0.2),
        ],
        "placements": [
            GenPlacing(level=1, timings=[32*x for x in range(128//32)]),
            GenPlacing(level=2, timings=[32*x + 28 for x in range(128//32)]),
        ],
    },
    {
        "meta": {
            "name": "8beat 3level",
        },
        "selectors": [
            GenSelector(gen_type=Pattern, level=1),
            GenSelector(gen_type=Pattern, level=2),
            GenSelector(gen_type=Pattern, level=3),
            GenSelector(gen_type=Vfilter, level=1, p=0.2),
            GenSelector(gen_type=Vfilter, level=2, p=0.2),
            GenSelector(gen_type=Vfilter, level=3, p=0.2),

        ],
        "placements": [
            GenPlacing(level=1, timings=[32*x for x in range(128//32)]),
            GenPlacing(level=2, timings=[32*x + 28 for x in range(128//32)], trigger_on_change=True),
            GenPlacing(level=3, timings=[32*x + 30 for x in range(128//32)], trigger_on_change=True),
        ],
    },
    {
        "meta": {
            "name": "8beat 3level fast switching",
        },
        "selectors": [
            GenSelector(gen_type=Pattern, level=1),
            GenSelector(gen_type=Pattern, level=2),
            GenSelector(gen_type=Pattern, level=3),
            GenSelector(gen_type=Vfilter, level=1, p=0.2),
            GenSelector(gen_type=Vfilter, level=2, p=0.2),
            GenSelector(gen_type=Vfilter, level=3, p=0.2),

        ],
        "placements": [
            GenPlacing(level=1, timings=[8*x for x in range(128//8)]),
            GenPlacing(level=2, timings=[8*x + 2 for x in range(128//8)], trigger_on_change=True),
            GenPlacing(level=3, timings=[8*x + 4 for x in range(128//8)], trigger_on_change=True),
        ],
    },
]
