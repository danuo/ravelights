from typing import TYPE_CHECKING

from loguru import logger
from ravelights.configs.components import blueprint_timelines
from ravelights.core.color_handler import ColorHandler
from ravelights.core.device import Device
from ravelights.core.settings import Settings
from ravelights.core.time_handler import BeatStatePattern, TimeHandler
from ravelights.core.utils import get_random_from_weights, p

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


class AutoPilot:
    """auto_loop_length [in beats]: randomized is called every n beats"""

    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings: Settings = self.root.settings
        self.devices: list[Device] = self.root.devices
        self.timehandler: TimeHandler = self.root.time_handler

    def randomize(self) -> None:
        """Called every frame to randomize parameters within ravelights app."""

        if not self.settings.enable_autopilot:
            return None

        beat_pattern = BeatStatePattern(loop_length=self.settings.auto_loop_length)
        if not beat_pattern.is_match(self.timehandler.beat_state):
            return None

        logger.info("run randomize routine")

        # ---------------------------------- colors ---------------------------------- #

        if self.settings.auto_color_primary:
            if p(self.settings.auto_p_color_primary):
                random_color = ColorHandler.get_random_color()
                logger.info("set new color_primary")
                self.settings.color_engine.set_color_with_rule(color=random_color, color_key="A")

        # --------------------------------- triggers --------------------------------- #

        if self.settings.auto_triggers:
            for device_index, device in enumerate(self.devices):
                if device.device_settings.linked_to is not None:
                    continue

                for gen_type in ("pattern", "pattern_sec", "pattern_break", "vfilter", "dimmer", "thinner"):
                    for timeline_level in range(1, 4):  # levels 1 to 4
                        if p(self.settings.auto_p_triggers):
                            logger.info(f"renew_trigger() with {device_index=} {gen_type=} {timeline_level=}")
                            self.settings.renew_trigger(
                                device_index=device_index,
                                gen_type=gen_type,
                                timeline_level=timeline_level,
                            )

        # --------------------------------- timeline --------------------------------- #

        if self.settings.auto_timeline_placement:
            if p(self.settings.auto_p_timeline_placement):
                timeline_weights: list[float | int] = [blue["meta"].weight for blue in blueprint_timelines]
                timeline_indices = list(range(len(timeline_weights)))
                new_timeline_index = get_random_from_weights(timeline_indices, timeline_weights)
                assert isinstance(new_timeline_index, int)
                self.root.pattern_scheduler.load_timeline_by_index(new_timeline_index)
