from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger
from ravelights.configs.components import blueprint_timelines
from ravelights.core.color_handler import ColorHandler
from ravelights.core.custom_typing import Slider, ToggleSlider
from ravelights.core.device import Device
from ravelights.core.settings import Settings
from ravelights.core.time_handler import BeatStatePattern, TimeHandler
from ravelights.core.utils import get_random_from_weights, p

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


CONTROLS_AUTOPILOT: list[Slider | ToggleSlider] = [
    ToggleSlider(
        name_toggle="renew_pattern",
        name_slider="p_renew_pattern",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        name_toggle="renew_pattern_sec",
        name_slider="p_renew_pattern_sec",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        name_toggle="renew_vfilter",
        name_slider="p_renew_vfilter",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        name_toggle="renew_dimmer",
        name_slider="p_renew_dimmer",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        name_toggle="renew_thinner",
        name_slider="p_renew_thinner",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        name_toggle="color_primary",
        name_slider="p_color_primary",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        name_toggle="timeline_placement",
        name_slider="p_timeline_placement",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        name_toggle="timeline_selector",
        name_slider="p_timeline_selector",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    Slider(
        name_slider="p_timeline_selector_individual",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        name_toggle="alternate",
        name_slider="p_alternate",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        name_toggle="triggers",
        name_slider="p_triggers",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    Slider(
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
            timeline_placement=True,  # full timeline
            p_timeline_placement=0.1,
            timeline_selector=True,
            p_timeline_selector=0.1,
            p_timeline_selector_individual=0.1,
            alternate=True,
            p_alternate=0.1,  # run on every item in selected seperately
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

        # ---------------------------------- colors ---------------------------------- #

        if self.settings.settings_autopilot["color_primary"]:
            if p(self.settings.settings_autopilot["p_color_primary"]):
                random_color = ColorHandler.get_random_color()
                logger.info("set new color_primary")
                self.settings.color_engine.set_color_with_rule(color=random_color, color_key="A")

        # --------------------------------- triggers --------------------------------- #

        if self.settings.settings_autopilot["triggers"]:
            for device_index, device in enumerate(self.devices):
                if device.linked_to is not None:
                    continue

                for gen_type in ("pattern", "pattern_sec", "pattern_break", "vfilter", "dimmer", "thinner"):
                    for timeline_level in range(1, 4):  # levels 1 to 4
                        if p(self.settings.settings_autopilot["p_triggers"]):
                            logger.info(f"renew_trigger() with {device_index=} {gen_type=} {timeline_level=}")
                            self.settings.renew_trigger(
                                device_index=device_index,
                                gen_type=gen_type,
                                timeline_level=timeline_level,
                            )

        # --------------------------------- timeline --------------------------------- #

        if self.settings.settings_autopilot["timeline_placement"]:
            if p(self.settings.settings_autopilot["p_timeline_placement"]):
                timeline_weights: list[float | int] = [blue["meta"].weight for blue in blueprint_timelines]
                timeline_indices = list(range(len(timeline_weights)))
                new_timeline_index = get_random_from_weights(timeline_indices, timeline_weights)
                self.root.pattern_scheduler.load_timeline_by_index(new_timeline_index)
