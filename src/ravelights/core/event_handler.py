from typing import TYPE_CHECKING, Any

from loguru import logger
from ravelights.core.effect_handler import EffectHandler
from ravelights.core.pattern_scheduler import PatternScheduler
from ravelights.core.settings import Settings
from ravelights.core.time_handler import TimeHandler

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


class EventHandler:
    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.root.time_handler
        self.devices = self.root.devices
        self.patternscheduler: PatternScheduler = self.root.pattern_scheduler
        self.effecthandler: EffectHandler = self.root.effect_handler
        self.modification_queue: list[dict[str, Any]] = []

    def add_to_modification_queue(self, receive_data: dict[str, Any]) -> None:
        """Queue incomming api calls here to be processed later at the beginning of a frame cycle."""
        self.modification_queue.append(receive_data)

    def apply_settings_modifications_queue(self) -> None:
        while self.modification_queue:
            receive_data: dict[str, Any] = self.modification_queue.pop()
            match receive_data:
                case {
                    "action": "gen_command",
                    "device_index": device_index,
                    "gen_type": gen_type,
                    "timeline_level": timeline_level,
                    "command": "renew_trigger",
                }:
                    logger.debug(f"gen_command with {gen_type} at level {timeline_level} and command renew_trigger")
                    device = self.devices[0]
                    assert timeline_level in [1, 2, 3]
                    if timeline_level is None:  # None means auto
                        timeline_level = device.get_effective_timeline_level()
                    self.settings.renew_trigger(
                        device_index=device_index,
                        gen_type=gen_type,
                        timeline_level=timeline_level,
                    )

                case {
                    "action": "gen_command",
                    "device_index": device_index,
                    "gen_type": gen_type,
                    "timeline_level": timeline_level,
                    "command": command,
                }:
                    logger.debug(f"gen_command with {gen_type} at level {timeline_level} and command {command}")
                    assert timeline_level in [1, 2, 3]

                    device = self.devices[device_index]

                    if timeline_level is None:
                        timeline_level = device.get_effective_timeline_level()
                    generator = device.rendermodule.get_selected_generator(
                        gen_type=gen_type, timeline_level=timeline_level
                    )
                    function = getattr(generator, command)
                    function()

                case {"action": "set_sync"}:
                    logger.debug("api: set_sync")
                    self.timehandler.bpm_sync()

                case {"action": "adjust_sync", "value": value}:
                    assert isinstance(value, float)
                    logger.debug(f"api: adjust_sync with {value=}")
                    self.timehandler.time_sync += value

                case {"action": "reset_color_mappings"}:
                    logger.debug("api: reset_color_mappings")
                    self.settings.reset_color_mapping()

                case {"action": "set_settings", "color_transition_speed": speed_str}:
                    logger.debug(f"api: set_settings color_transition_speed {speed_str}")
                    if isinstance(speed_str, str):
                        self.settings.set_color_transition_speed(speed_str)
                    else:
                        logger.error("could not apply color_transition_speed, value is not a string")

                case {"action": "set_settings", **other_kwargs}:
                    logger.debug(f"api: set_settings {other_kwargs}")
                    self.settings.update_from_dict(other_kwargs)

                case {"action": "set_settings_autopilot", **other_kwargs}:
                    logger.debug("api: set_settings_autopilot (...)")
                    self.settings.set_settings_autopilot(other_kwargs)

                case {"action": "set_device_settings", "device_index": device_index, **other_kwargs}:
                    logger.debug(f"api: set_device_settings with {device_index=}")
                    assert isinstance(device_index, int) or device_index is None
                    if isinstance(device_index, int):
                        self.devices[device_index].update_from_dict(other_kwargs)
                    else:
                        for device in self.devices:
                            device.update_from_dict(other_kwargs)

                case {"action": "set_trigger", "device_index": device_index, **other_kwargs}:
                    logger.debug(f"api: set_trigger with {other_kwargs}")
                    self.settings.set_trigger(new_trigger=other_kwargs, device_index=device_index, **other_kwargs)

                case {"action": "set_generator", **other_kwargs}:
                    logger.debug(f"api: set_generator with {other_kwargs}")
                    renew_trigger = self.settings.renew_trigger_from_manual
                    assert isinstance(other_kwargs["device_index"], int), other_kwargs["device_index"]
                    assert other_kwargs["timeline_level"] is None or 1 <= other_kwargs["timeline_level"] <= 3
                    self.settings.set_generator(renew_trigger=renew_trigger, **other_kwargs)

                case {
                    "action": "set_timeline",
                    "timeline_index": timeline_index,
                    "placements": placements,
                    "selectors": selectors,
                }:
                    logger.debug(f"api: set_timeline with {timeline_index=}, {placements=} and {selectors=}")
                    self.patternscheduler.load_timeline_from_index(
                        index=int(timeline_index),
                        placements=placements,
                        selectors=selectors,
                    )

                case {"action": "clear_effect_queue"}:
                    self.effecthandler.clear_qeueues()
                    logger.debug("api: cleared all effect queues")

                case {
                    "action": "set_effect",
                    "mode": "frames",
                    "effect_name": effect_name,
                    "limit_frames": limit_frames,
                    "multi": multi,
                    "frames_pattern": frames_pattern,
                }:
                    self.effecthandler.load_effect_frames(
                        effect_name=effect_name,
                        limit_frames=limit_frames,
                        multi=multi,
                        frames_pattern=frames_pattern,
                    )

                case {
                    "action": "set_effect",
                    "mode": "quarters",
                    "effect_name": effect_name,
                    "limit_quarters": limit_quarters,
                    "multi": multi,
                    "frames_pattern": frames_pattern,
                }:
                    self.effecthandler.load_effect_quarters(
                        effect_name=effect_name,
                        limit_quarters=limit_quarters,
                        multi=multi,
                        frames_pattern=frames_pattern,
                    )

                case {
                    "action": "set_effect",
                    "mode": "frames",
                    "effect_name": effect_name,
                }:
                    logger.error("should not be used")
                    logger.debug(f"api: set_effect: {other_kwargs}")
                    self.effecthandler.load_effect(**other_kwargs)

                case {
                    "action": "modify_effect",
                    "operation": operation,
                    "effect_name": effect_name,
                }:
                    assert isinstance(effect_name, str)
                    match operation:
                        case "renew_trigger":
                            logger.debug(f"api: modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_renew_trigger(effect=effect_name)
                        case "alternate":
                            logger.debug(f"api: modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_alternate(effect=effect_name)
                        case "remove":
                            logger.debug(f"api: modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_remove(effect=effect_name)
                        case _:
                            logger.warning(
                                f"api: instruction with 'action': 'modify_effect' and {operation=} not understood"
                            )

                case {"action": "set_color", "color_rgb": color_rgb, "color_key": color_key}:
                    self.settings.color_engine.set_color_with_rule(color=color_rgb, color_key=color_key)

                case other:
                    logger.error(f"api: instruction not understood: {other=}")
