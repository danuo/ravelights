import logging
from dataclasses import InitVar, dataclass, field
from enum import Enum
from typing import Optional, Type

from ravelights.core.bpmhandler import BeatState, BeatStatePattern, BPMhandler
from ravelights.core.colorhandler import COLOR_TRANSITION_SPEEDS, Color, ColorEngine, ColorHandler
from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
from ravelights.core.timehandler import TimeHandler
from ravelights.effects.effect_super import Effect

T_JSON = dict[str, str | float | int | bool]
logger = logging.getLogger(__name__)


class MusicStyles(Enum):
    """available music styles for settings"""

    TECHNO = "techno"
    DISCO = "disco"
    AMBIENT = "ambient"


class SecondaryColorModes(Enum):
    """available modes to generate secondary color for settings"""

    # todo. replace with StrEnum and auto() with python 11
    RANDOM = "random"
    COMPLEMENTARY = "complementary"
    COMPLEMENTARY33 = "complementary33"
    COMPLEMENTARY50 = "complementary50"
    COMPLEMENTARY66 = "complementary66"


def get_default_selected_dict() -> dict[str, list[str]]:
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
        "effect": [BeatStatePattern(p=1.0) for _ in range(5)],
    }


@dataclass
class Settings:
    """
    Holds global parameters that can be accessed by all other components.
    Public attributes can be modified at any time.
    """

    device_config: InitVar = None

    # ─── Meta Information ─────────────────────────────────────────────────
    generator_classes_identifiers: list[str] = field(init=False)
    controls: dict = field(default_factory=dict)  # holds meta data to create controls in ui dynamically
    meta: dict = field(default_factory=dict)

    # ─── Device Configuration ─────────────────────────────────────────────
    light_setup: list[dict] = field(init=False)
    lights_per_output: list[int] = field(init=False)

    # ─── Color Settings ───────────────────────────────────────────────────
    color_transition_speed: str = COLOR_TRANSITION_SPEEDS[1].value  # =fast
    color_sec_active: bool = True  # to apply secondary color mode
    color_sec_mode: str = SecondaryColorModes.COMPLEMENTARY.value
    color_sec_mode_names: list[str] = field(default_factory=lambda: [mode.value for mode in SecondaryColorModes])
    color_names: list[str] = field(default_factory=lambda: ["primary", "secondary", "effect"])
    global_brightness: float = 1.0
    global_thinning_ratio: float = 0.5
    global_energy: float = 0.5
    global_skip_trigger: int = 2

    global_pattern_sec: bool = False
    global_vfilter: bool = False
    global_thinner: bool = False
    global_dimmer: bool = False
    load_thinner_with_pat: bool = False
    load_dimmer_with_pat: bool = False
    load_triggers_with_gen: bool = False
    music_style: str = MusicStyles.TECHNO.value

    # ─── Time Settings ────────────────────────────────────────────────────
    bpm_base: float = 140.0
    bpm_multiplier: float = 1.0
    fps: int = 20
    queue_length: int = 32 * 4
    frame_skip: int = 1  # must be >= 1

    # ─── Pattern Settings ─────────────────────────────────────────────────
    selected: dict[str, list[str]] = field(default_factory=get_default_selected_dict)
    triggers: dict[str, list[BeatStatePattern]] = field(default_factory=get_default_triggers)
    active_timeline_index: int = 1  # default timeline index
    use_manual_timeline: bool = True
    manual_timeline_level: int = 1

    # ─── Other Settings ───────────────────────────────────────────────────
    settings_autopilot: dict = field(init=False)

    def __post_init__(self, device_config):
        # assert device_config
        if device_config:  # why is this optional?
            # self.device_config = device_config
            self.light_setup: list[dict] = device_config["light_setup"]
            self.calc_lights_per_output(device_config)

        self.color_engine = ColorEngine(settings=self)
        self.generator_classes = [Pattern, Vfilter, Thinner, Dimmer, Effect]
        self.generator_classes_identifiers = [c.get_identifier() for c in self.generator_classes]
        self.generator_classes_identifiers.insert(1, self.generator_classes[0].get_identifier() + "_sec")

        self.timehandler = TimeHandler(settings=self)
        self.bpmhandler = BPMhandler(settings=self, timehandler=self.timehandler)

    def calc_lights_per_output(self, device_config):
        self.lights_per_output = [d["n_leds"] * d["n_lights"] for d in self.light_setup] + [0 for _ in range(4 - len(self.light_setup))]

    def clear_selected(self):
        """resets selected generators to default state"""
        self.selected = get_default_selected_dict()

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

    def set_color_fade(self, color: list | Color, level):
        assert len(color) == 3
        color = ColorHandler.convert_to_color(color)
        self.color_engine.set_color_rgb(color, level)
        if level == 0 and self.color_sec_active:
            sec_color = self.get_secondary_color(color)
            self.color_engine.set_color_rgb(sec_color, 1)

    def apply_secondary_color_rule(self):
        """call this when secondary rule changes"""
        # todo
        assert False
        primary_color = self.color[0]
        secondary_color = self.get_secondary_color(primary_color)
        self.color[1] = secondary_color

    def get_secondary_color(self, in_color: Color) -> Optional[Color]:
        # todo: move this to colorhandler
        """returns a color that matches in input color, according to the secondary
        color rule currently selected in settings"""

        match SecondaryColorModes(self.color_sec_mode):
            case SecondaryColorModes.COMPLEMENTARY:
                return ColorHandler.get_complementary_color(in_color)
            case SecondaryColorModes.COMPLEMENTARY33:
                return ColorHandler.get_complementary_33(in_color)
            case SecondaryColorModes.COMPLEMENTARY50:
                return ColorHandler.get_complementary_50(in_color)
            case SecondaryColorModes.COMPLEMENTARY66:
                return ColorHandler.get_complementary_66(in_color)
            case SecondaryColorModes.RANDOM:
                return ColorHandler.get_random_color()

    @property
    def frame_time(self) -> float:
        return 1 / self.fps

    def update_from_dict(self, update_dict: T_JSON) -> None:
        assert isinstance(update_dict, dict)
        for key, value in update_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_generator(self, gen_type: str | Type["Generator"], level_index: int, gen_name: str):
        gen_type = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        logger.debug(f"set_generator with {gen_type} {level_index} {gen_name}")
        self.selected[gen_type][level_index] = gen_name

    def set_trigger(self, gen_type: str | Type["Generator"], level_index: int, **kwargs) -> None:
        gen_type = gen_type if isinstance(gen_type, str) else gen_type.get_identifier()
        logger.debug(f"set_trigger with {gen_type} {level_index} {kwargs}")
        self.triggers[gen_type][level_index].update_from_dict(kwargs)

    def before(self):
        self.timehandler.before()
        self.color_engine.run_pid_step()

    def after(self):
        self.timehandler.after()
