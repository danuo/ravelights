import logging
from dataclasses import InitVar, asdict, dataclass, field
from enum import auto
from typing import TYPE_CHECKING, Any, Optional, Type

from ravelights.core.bpmhandler import BeatState, BeatStatePattern, BPMhandler
from ravelights.core.colorhandler import COLOR_TRANSITION_SPEEDS, ColorEngine, SecondaryColorModes
from ravelights.core.device_shared import DeviceLightConfig
from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
from ravelights.core.timehandler import TimeHandler
from ravelights.core.utils import StrEnum
from ravelights.effects.effect_super import Effect

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp

logger = logging.getLogger(__name__)


class MusicStyles(StrEnum):
    """available music styles for settings"""

    TECHNO = auto()
    DISCO = auto()
    AMBIENT = auto()


def get_default_selected_dict() -> dict[str, list[str]]:
    """
    level 0: none
    level 1: 1
    level 2: 2
    level 3: 3
    level 4: not used
    """
    return {
        Pattern.get_identifier(): ["p_none" for _ in range(5)],
        Pattern.get_identifier() + "_sec": ["p_none" for _ in range(5)],
        Vfilter.get_identifier(): ["v_none" for _ in range(5)],
        Thinner.get_identifier(): ["t_none" for _ in range(5)],
        Dimmer.get_identifier(): ["d_none" for _ in range(5)],
    }


def get_default_triggers() -> dict[str, list[BeatStatePattern]]:
    return {
        Pattern.get_identifier(): [BeatStatePattern(beats=[0, 3], quarters="AC", loop_length=8) for _ in range(5)],
        Pattern.get_identifier() + "_sec": [BeatStatePattern() for _ in range(5)],
        Vfilter.get_identifier(): [BeatStatePattern() for _ in range(5)],
        Thinner.get_identifier(): [BeatStatePattern() for _ in range(5)],
        Dimmer.get_identifier(): [BeatStatePattern() for _ in range(5)],
    }


def get_default_color_mappings() -> dict[str, dict[str, str]]:
    """
    level 1,2,3
    primary, secondary
    select colors from A, B, C
    """

    return {
        "1": {
            "prim": "A",
            "sec": "B",
        },
        "2": {
            "prim": "B",
            "sec": "A",
        },
        "3": {
            "prim": "C",
            "sec": "A",
        },
    }


def get_default_color_sec_modes() -> dict[str, str]:
    return {"B": SecondaryColorModes.COMPLEMENTARY.value, "C": SecondaryColorModes.COMPLEMENTARY66.value}


@dataclass
class Settings:
    """
    Holds global parameters that can be accessed by all other components.
    Public attributes can be modified at any time.
    """

    # ─── Device Configuration ─────────────────────────────────────────────
    root_init: InitVar["RaveLightsApp"]
    device_config: list[DeviceLightConfig]

    # ─── Meta Information ─────────────────────────────────────────────────
    generator_classes_identifiers: list[str] = field(init=False)

    # ─── Color Settings ───────────────────────────────────────────────────
    color_transition_speed: str = COLOR_TRANSITION_SPEEDS[1].value  # =fast
    color_sec_mode: dict[str, str] = field(default_factory=get_default_color_sec_modes)
    color_mapping: dict[str, dict[str, str]] = field(default_factory=get_default_color_mappings)
    global_brightness: float = 1.0
    global_thinning_ratio: float = 0.5
    global_energy: float = 0.5
    global_triggerskip: int = 1

    # ─── Effect Settings ──────────────────────────────────────────────────

    global_effects_enabled: bool = True
    global_effect_draw_mode: str = "normal"  # "overlay" or "normal"
    effect_draw_mode: str = "normal"  # "overlay" or "normal"

    # ─── Generator Settings ────────────────────────────────────────────────

    global_pattern_sec: bool = False
    global_vfilter: bool = False
    global_thinner: bool = False
    global_dimmer: bool = False
    music_style: str = MusicStyles.TECHNO.value

    # ─── Time Settings ────────────────────────────────────────────────────
    bpm_base: float = 140.0
    bpm_multiplier: float = 1.0
    fps: int = 20
    queue_length: int = 32 * 4
    global_frameskip: int = 1  # must be >= 1

    # ─── Autoloading ──────────────────────────────────────────────────────
    renew_trigger_from_manual: bool = True
    renew_thinner_from_manual: bool = True
    renew_dimmer_from_manual: bool = True
    renew_trigger_from_timeline: bool = True

    # ─── Pattern Settings ─────────────────────────────────────────────────
    selected: dict[str, list[str]] = field(default_factory=get_default_selected_dict)

    active_timeline_index: int = 0  # default timeline index
    use_manual_timeline: bool = True
    global_manual_timeline_level: int = 1

    websocket_data: tuple[int, ...] = (30, 10, 10)

    # ─── Other Settings ───────────────────────────────────────────────────
    settings_autopilot: dict[str, Any] = field(init=False)

    def __post_init__(self, root_init: "RaveLightsApp"):
        self.root = root_init
        self.generator_classes = [Pattern, Vfilter, Thinner, Dimmer, Effect]
        self.generator_classes_identifiers = [c.get_identifier() for c in self.generator_classes]
        self.generator_classes_identifiers.insert(1, self.generator_classes[0].get_identifier() + "_sec")

        self.timehandler = TimeHandler(settings=self)
        self.bpmhandler = BPMhandler(settings=self, timehandler=self.timehandler)

        self.color_engine = ColorEngine(settings=self)
        self.triggers: dict[str, list[BeatStatePattern]] = get_default_triggers()

    def clear_selected(self):
        """resets selected generators to default state"""
        self.selected = get_default_selected_dict()
        self.root.refresh_ui(sse_event="settings")

    @property
    def bpm(self) -> float:
        return self.bpm_multiplier * self.bpm_base

    @property
    def beat_state(self) -> BeatState:
        return self.bpmhandler.beat_state

    @property
    def beat_time(self) -> float:
        """time of a beat in seconds"""
        return 60 / self.bpm

    @property
    def quarter_time(self) -> float:
        """time of a quarter in seconds"""
        return 60 / (self.bpm * 4)

    @property
    def n_quarters(self) -> int:
        """self.n_quarters: will always represent current quarter number [0,15]"""
        return self.n_quarters_long % 16

    @property
    def n_quarters_long(self) -> int:
        """self.n_quarters: will always represent current quarter number [0,127]"""
        return self.beat_state.n_quarters_long

    @property
    def beat_progress(self) -> float:
        return self.beat_state.beat_progress

    @property
    def frame_time(self) -> float:
        return 1 / self.fps

    def update_from_dict(self, update_dict: dict[str, Any]) -> None:
        assert isinstance(update_dict, dict)
        for key, value in update_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"successfully set {key} with {value}")
            else:
                logger.warning(f"key {key} does not exist in settings")
        self.root.refresh_ui(sse_event="settings")

    def set_generator(self, gen_type: str | Type["Generator"], timeline_level: int, gen_name: str, renew_trigger: bool):
        gen_type = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        if timeline_level == 0:
            timeline_level = self.global_manual_timeline_level
            if timeline_level == 0:
                timeline_level = 1
            if gen_type == "vfilter" and self.global_vfilter:
                timeline_level = 1
            elif gen_type == "thinner" and self.global_thinner:
                timeline_level = 1
            elif gen_type == "dimmer" and self.global_dimmer:
                timeline_level = 1
        self.selected[gen_type][timeline_level] = gen_name
        if renew_trigger:
            self.renew_trigger(gen_type=gen_type, timeline_level=timeline_level)
        self.root.refresh_ui(sse_event="settings")

    def renew_trigger(self, gen_type: str | Type["Pattern"], timeline_level: int):
        generator = self.root.devices[0].rendermodule.get_selected_generator(
            gen_type=gen_type, timeline_level=timeline_level
        )
        new_trigger = generator.get_new_trigger()
        self.set_trigger(gen_type=gen_type, timeline_level=timeline_level, beatstate_pattern=new_trigger)
        self.root.refresh_ui(sse_event="triggers")

    def set_trigger(
        self,
        gen_type: str | Type["Generator"],
        timeline_level: int,
        beatstate_pattern: Optional[BeatStatePattern] = None,
        **kwargs: dict[str, Any],
    ):
        """triggers can be updated by new BeatStatePattern object or via keywords (kwargs)"""
        if beatstate_pattern is not None:
            kwargs.update(asdict(beatstate_pattern))
        gen_type = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        logger.debug(f"set_trigger with {gen_type} {timeline_level}")
        self.triggers[gen_type][timeline_level].update_from_dict(kwargs)
        self.root.refresh_ui(sse_event="triggers")

    def set_settings_autopilot(self, in_dict):
        self.settings_autopilot.update(in_dict)
        self.root.refresh_ui(sse_event="settings")

    def reset_color_mapping(self):
        self.color_mapping = get_default_color_mappings()
        self.root.refresh_ui(sse_event="settings")

    def set_color_transition_speed(self, speed: str):
        self.color_transition_speed = speed
        self.color_engine.set_color_speed(speed)
        self.root.refresh_ui(sse_event="settings")

    def before(self):
        self.timehandler.before()
        self.color_engine.before()

    def after(self):
        self.timehandler.after()
