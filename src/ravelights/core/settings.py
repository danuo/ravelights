from dataclasses import InitVar, asdict, dataclass, field
from enum import auto
from typing import TYPE_CHECKING, Any, Literal, Optional

from loguru import logger
from ravelights.core.color_handler import COLOR_TRANSITION_SPEEDS, ColorEngine, SecondaryColorModes
from ravelights.core.device_shared import DeviceLightConfig
from ravelights.core.generator_super import Dimmer, Pattern, Thinner, Vfilter
from ravelights.core.time_handler import BeatStatePattern
from ravelights.core.utils import StrEnum

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


class MusicStyle(StrEnum):
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
    root_init: InitVar["RaveLightsApp"]  # todo: remove this
    device_config: list[DeviceLightConfig]

    # ─── App ──────────────────────────────────────────────────────────────
    use_audio: bool
    use_visualizer: bool
    print_stats: bool
    serve_webui: bool

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
    global_effect_draw_mode: Literal["normal", "overlay"] = "normal"
    effect_draw_mode: Literal["normal", "overlay"] = "normal"

    # ─── Generator Settings ────────────────────────────────────────────────

    global_pattern_sec: bool = False
    global_vfilter: bool = False
    global_thinner: bool = False
    global_dimmer: bool = False
    music_style: Optional["MusicStyle"] = None

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

    active_timeline_index: int = 0
    use_manual_timeline: bool = True
    global_manual_timeline_level: int = 1

    websocket_data: tuple[int, ...] = (30, 10, 10)

    # ─── Other Settings ───────────────────────────────────────────────────
    settings_autopilot: dict[str, Any] = field(init=False)

    def __post_init__(self, root_init: "RaveLightsApp") -> None:
        self.root = root_init
        self.generator_classes_identifiers = ["pattern", "pattern_sec", "vfilter", "thinner", "dimmer", "effect"]

        self.color_engine = ColorEngine(settings=self)
        self.triggers: dict[str, list[BeatStatePattern]] = get_default_triggers()

    def clear_selected(self) -> None:
        """resets selected generators to default state"""
        logger.debug("clear_selected")
        self.selected = get_default_selected_dict()
        self.root.refresh_ui(sse_event="settings")

    def update_from_dict(self, update_dict: dict[str, Any]) -> None:
        """overwritte settings with new values from a dict"""
        logger.debug(f"update_from_dict with {update_dict=}")
        assert isinstance(update_dict, dict)
        for key, value in update_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"successfully set {key} with {value}")
            else:
                logger.warning(f"key {key} does not exist in settings")
        self.root.refresh_ui(sse_event="settings")

    def set_generator(
        self,
        gen_type: Literal["pattern", "pattern_sec", "vfilter", "dimmer", "thinner"],
        timeline_level: int,
        gen_name: str,
        renew_trigger: bool,
    ) -> None:
        logger.debug(f"set_generator with {gen_type=} {timeline_level=} {gen_name=} {renew_trigger=}")
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

    def renew_trigger(
        self,
        gen_type: Literal["pattern", "pattern_sec", "vfilter", "dimmer", "thinner"],
        timeline_level: int,
    ) -> None:
        generator = self.root.devices[0].rendermodule.get_selected_generator(
            gen_type=gen_type, timeline_level=timeline_level
        )
        logger.debug(f"renew_trigger with {gen_type=} {timeline_level=}")
        new_trigger = generator.get_new_trigger()
        self.set_trigger(gen_type=gen_type, timeline_level=timeline_level, beatstate_pattern=new_trigger)
        self.root.refresh_ui(sse_event="triggers")

    def set_trigger(
        self,
        gen_type: Literal["pattern", "pattern_sec", "vfilter", "dimmer", "thinner"],
        timeline_level: int,
        beatstate_pattern: Optional[BeatStatePattern] = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """triggers can be updated by new BeatStatePattern object or via keywords (kwargs)"""
        logger.debug(f"set_trigger with {gen_type=} {timeline_level=}")
        if beatstate_pattern is not None:
            kwargs.update(asdict(beatstate_pattern))
        self.triggers[gen_type][timeline_level].update_from_dict(kwargs)
        self.root.refresh_ui(sse_event="triggers")

    def set_settings_autopilot(self, in_dict) -> None:
        logger.debug(f"set_settings_autopilot with {in_dict=}")
        self.settings_autopilot.update(in_dict)
        self.root.refresh_ui(sse_event="settings")

    def reset_color_mapping(self) -> None:
        logger.debug("reset_color_mapping")
        self.color_mapping = get_default_color_mappings()
        self.root.refresh_ui(sse_event="settings")

    def set_color_transition_speed(self, speed: str) -> None:
        logger.debug(f"reset_color_mapping with {speed=}")
        self.color_transition_speed = speed
        self.color_engine.set_color_speed(speed)
        self.root.refresh_ui(sse_event="settings")
