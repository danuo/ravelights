from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger
from ravelights.core.color_handler import ColorHandler
from ravelights.core.custom_typing import Slider, ToggleSlider
from ravelights.core.device import Device
from ravelights.core.settings import Settings
from ravelights.core.time_handler import BeatStatePattern, TimeHandler
from ravelights.core.utils import p

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


AUTOPILOT_CONTROLS: list[Slider | ToggleSlider] = [
    ToggleSlider(
        type="toggle_slider",
        name_toggle="renew_pattern",
        name_slider="p_renew_pattern",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        type="toggle_slider",
        name_toggle="renew_pattern_sec",
        name_slider="p_renew_pattern_sec",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        type="toggle_slider",
        name_toggle="renew_vfilter",
        name_slider="p_renew_vfilter",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        type="toggle_slider",
        name_toggle="renew_dimmer",
        name_slider="p_renew_dimmer",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        type="toggle_slider",
        name_toggle="renew_thinner",
        name_slider="p_renew_thinner",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        type="toggle_slider",
        name_toggle="color_primary",
        name_slider="p_color_primary",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        type="toggle_slider",
        name_toggle="timeline",
        name_slider="p_timeline",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        type="toggle_slider",
        name_toggle="alternate_pattern",
        name_slider="p_alternate_pattern",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        type="toggle_slider",
        name_toggle="alternate_pattern_sec",
        name_slider="p_alternate_pattern_sec",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        type="toggle_slider",
        name_toggle="triggers",
        name_slider="p_triggers",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    Slider(
        type="slider",
        name_slider="autopilot_loop_length",
        range_min=4,
        range_max=32,
        step=4,
        markers=True,
    ),
]


@dataclass
class AutoPilot:
    """
    autopilot_loop_length [in beats]: randomized is called every n beats
    """

    root: "RaveLightsApp"

    def __post_init__(self) -> None:
        self.settings: Settings = self.root.settings
        self.devices: list[Device] = self.root.devices
        self.timehandler: TimeHandler = self.root.time_handler

        self.settings.settings_autopilot = dict(
            autopilot_loop_length=4,
            renew_pattern=True,
            p_renew_pattern=0.1,  # use in timeline genselector
            renew_pattern_sec=True,
            p_renew_pattern_sec=0.1,  # use in timeline genselector
            renew_vfilter=True,
            p_renew_vfilter=0.1,  # use in timeline genselector
            renew_thinner=True,
            p_renew_thinner=0.1,  # use in timeline genselector
            renew_dimmer=True,
            p_renew_dimmer=0.1,  # use in timeline genselector
            color_primary=True,
            p_color_primary=0.1,
            timeline=True,
            p_timeline=0.1,
            alternate_pattern=True,
            p_alternate_pattern=0.1,  # run on every item in selected seperately
            alternate_pattern_sec=True,
            p_alternate_pattern_sec=0.1,  # run on every item in selected seperately
            triggers=True,
            p_triggers=0.1,  # run on every item in selected seperately
        )

    def randomize(self) -> None:
        """Called every frame to randomize parameters within ravelights app."""

        if not self.settings.enable_autopilot:
            return None

        beat_pattern = BeatStatePattern(loop_length=self.settings.settings_autopilot["autopilot_loop_length"])
        if not beat_pattern.is_match(self.timehandler.beat_state):
            return None

        logger.info("run randomize routine")

        # ─── Colors ───────────────────────────────────────────────────

        if self.settings.settings_autopilot["color_primary"]:
            if p(self.settings.settings_autopilot["p_color_primary"]):
                random_color = ColorHandler.get_random_color()
                logger.info("set new color_primary")
                self.settings.color_engine.set_color_with_rule(color=random_color, color_key="A")

        # ─── Triggers ─────────────────────────────────────────────────

        if self.settings.settings_autopilot["triggers"]:
            for gen_type in ["pattern", "pattern_sec", "vfilter", "dimmer", "thinner"]:
                for timeline_level in range(1, 4):  # levels 1 to 4
                    if p(self.settings.settings_autopilot["p_triggers"]):
                        logger.info(f"renew_trigger {gen_type} {timeline_level}")
                        logger.warning("this is not done")
                        # todo: make sure correct device is
                        # self.settings.renew_trigger(gen_type=gen_type, timeline_level=timeline_level)
