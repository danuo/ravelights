from dataclasses import InitVar, asdict, dataclass, field
from enum import auto
from typing import TYPE_CHECKING, Any, Literal, Optional

from loguru import logger
from ravelights.core.color_handler import COLOR_TRANSITION_SPEEDS, ColorEngine, SecondaryColorModes
from ravelights.core.device_shared import DeviceLightConfig
from ravelights.core.time_handler import BeatStatePattern
from ravelights.core.utils import StrEnum

if TYPE_CHECKING:
    from ravelights.configs.components import Keyword
    from ravelights.core.ravelights_app import RaveLightsApp


N_LEVELS = 4


class AutomateChorus(StrEnum):
    manual = auto()
    audio = auto()


def get_default_selected() -> dict[str, list[str]]:
    """
    level 0: none (black output)
    level 1: 1
    level 2: 2
    level 3: 3
    """
    return {
        "pattern": ["p_none" for _ in range(N_LEVELS)],
        "pattern_sec": ["p_none" for _ in range(N_LEVELS)],
        "pattern_break": ["p_none" for _ in range(N_LEVELS)],
        "vfilter": ["v_none" for _ in range(N_LEVELS)],
        "thinner": ["t_none" for _ in range(N_LEVELS)],
        "dimmer": ["d_none" for _ in range(N_LEVELS)],
    }


def get_default_triggers() -> dict[str, list[BeatStatePattern]]:
    return {
        "pattern": [BeatStatePattern(beats=[0, 3], quarters="AC", loop_length=8) for _ in range(N_LEVELS)],
        "pattern_sec": [BeatStatePattern() for _ in range(N_LEVELS)],
        "pattern_break": [BeatStatePattern() for _ in range(N_LEVELS)],
        "vfilter": [BeatStatePattern() for _ in range(N_LEVELS)],
        "thinner": [BeatStatePattern() for _ in range(N_LEVELS)],
        "dimmer": [BeatStatePattern() for _ in range(N_LEVELS)],
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
    n_devices: int = field(init=False)

    # ─── App ──────────────────────────────────────────────────────────────
    use_audio: bool
    use_visualizer: bool
    print_stats: bool
    serve_webui: bool

    # ─── Meta Information ─────────────────────────────────────────────────
    generator_classes_identifiers: tuple[str, ...] = (
        "pattern",
        "pattern_sec",
        "vfilter",
        "thinner",
        "dimmer",
        "effect",
    )

    # ─── Color Settings ───────────────────────────────────────────────────

    color_transition_speed: str = COLOR_TRANSITION_SPEEDS[1].value  # =fast
    color_sec_mode: dict[str, str] = field(default_factory=get_default_color_sec_modes)
    color_mapping: dict[str, dict[str, str]] = field(default_factory=get_default_color_mappings)
    global_brightness: float = 1.0
    global_thinning_ratio: float = 0.5
    global_energy: float = 0.5
    global_triggerskip: int = 1

    # ─── Chorus ───────────────────────────────────────────────────────────

    automate_chorus: AutomateChorus = AutomateChorus.manual
    global_manual_chorus: float = 1.0  # 1.0 -> main 0.0 -> break

    # ─── Effect Settings ──────────────────────────────────────────────────

    global_effects_enabled: bool = True

    # ─── Generator Settings ───────────────────────────────────────────────

    global_pattern_sec: bool = False
    global_pattern_break: bool = False
    global_vfilter: bool = False
    global_thinner: bool = False
    global_dimmer: bool = False
    music_style: Optional["Keyword"] = None

    # ─── Audio and Time Settings ──────────────────────────────────────────

    bpm_base: float = 140.0
    bpm_multiplier: float = 1.0
    fps: int = 20
    queue_length: int = 32 * 4
    global_frameskip: int = 1  # must be >= 1

    enable_audio_analysis: bool = True

    # ─── Autoloading ──────────────────────────────────────────────────────

    renew_trigger_from_manual: bool = True
    renew_thinner_from_manual: bool = True
    renew_dimmer_from_manual: bool = True
    renew_trigger_from_timeline: bool = True

    # ─── Pattern Settings ─────────────────────────────────────────────────

    selected: list[dict[str, list[str]]] = field(init=False)

    active_timeline_index: int = 0
    global_manual_timeline_level: Optional[int] = 1
    target_device_index: Optional[int] = 0

    # ─── Autopilot ────────────────────────────────────────────────────────

    enable_autopilot: bool = False
    settings_autopilot: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self, root_init: "RaveLightsApp") -> None:
        self.root = root_init
        self.color_engine = ColorEngine(settings=self)
        self.n_devices = len(self.device_config)
        self.reset_selected()
        self.triggers: list[dict[str, list[BeatStatePattern]]] = [
            get_default_triggers() for _ in range(self.n_devices)
        ]  # should not be part of asdict(self)

    def reset_selected(self) -> None:
        """resets selected generators to default state"""
        logger.debug("reset_selected")
        self.selected = [get_default_selected() for _ in range(self.n_devices)]
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
        device_index: int,
        gen_type: Literal["pattern", "pattern_sec", "pattern_break", "vfilter", "dimmer", "thinner"],
        timeline_level: Optional[int],
        gen_name: str,
        renew_trigger: bool,
    ) -> None:
        logger.debug(f"set_generator with {gen_type=} {timeline_level=} {gen_name=} {renew_trigger=}")
        assert timeline_level is None or timeline_level >= 1
        if timeline_level is None:
            return

        if gen_type == "vfilter" and self.global_vfilter:
            timeline_level = 1
        elif gen_type == "thinner" and self.global_thinner:
            timeline_level = 1
        elif gen_type == "dimmer" and self.global_dimmer:
            timeline_level = 1

        self.selected[device_index][gen_type][timeline_level] = gen_name
        if renew_trigger:
            self.renew_trigger(device_index=device_index, gen_type=gen_type, timeline_level=timeline_level)
        self.root.refresh_ui(sse_event="settings")

    def renew_trigger(
        self,
        device_index: int,
        gen_type: Literal["pattern", "pattern_sec", "pattern_break", "vfilter", "dimmer", "thinner"],
        timeline_level: int,
    ) -> None:
        generator = self.root.devices[0].rendermodule.get_selected_generator(
            device_index=device_index, gen_type=gen_type, timeline_level=timeline_level
        )
        logger.debug(f"renew_trigger with {gen_type=} {timeline_level=}")
        new_trigger = generator.get_new_trigger()
        self.set_trigger(
            device_index=device_index,
            gen_type=gen_type,
            timeline_level=timeline_level,
            new_trigger=new_trigger,
        )
        self.root.refresh_ui(sse_event="triggers")

    def set_trigger(
        self,
        device_index: int,
        gen_type: Literal["pattern", "pattern_sec", "pattern_break", "vfilter", "dimmer", "thinner"],
        timeline_level: int,
        new_trigger: BeatStatePattern | dict[str, Any],
    ) -> None:
        """triggers can be updated by new BeatStatePattern object or via keyword dict"""
        logger.debug(f"set_trigger with {gen_type=} {timeline_level=}")
        if isinstance(new_trigger, BeatStatePattern):
            new_trigger = asdict(new_trigger)
        self.triggers[device_index][gen_type][timeline_level].update_from_dict(new_trigger)
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
