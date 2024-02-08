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
        self.timehandler: TimeHandler = self.root.timehandler
        self.devices = self.root.devices
        self.patternscheduler: PatternScheduler = self.root.patternscheduler
        self.effecthandler: EffectHandler = self.root.effecthandler
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
                    device = self.patternscheduler.devices[0]
                    if timeline_level == 0:  # level = 0 means auto
                        timeline_level = device.rendermodule.get_timeline_level()
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
                    for device in self.patternscheduler.devices:
                        # todo: make sure this applied to correct devices
                        if timeline_level == 0:
                            timeline_level = device.rendermodule.get_timeline_level()
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
                    assert isinstance(device_index, int)
                    logger.debug(f"api: set_device_settings with {device_index}")
                    self.devices[device_index].update_from_dict(other_kwargs)
                case {"action": "set_trigger", **other_kwargs}:
                    logger.debug(f"api: set_trigger with {other_kwargs}")
                    self.settings.set_trigger(new_trigger=other_kwargs)
                case {"action": "set_generator", **other_kwargs}:
                    logger.debug(f"api: set_generator with {other_kwargs}")
                    renew_trigger = self.settings.renew_trigger_from_manual
                    assert isinstance(other_kwargs["device_index"], int), other_kwargs["device_index"]
                    assert other_kwargs["timeline_level"] is None or 1 <= other_kwargs["timeline_level"] <= 3
                    self.settings.set_generator(renew_trigger=renew_trigger, **other_kwargs)
                case {"action": "set_timeline", "timeline_index": index, "set_full": set_full}:
                    # if set_full:     load generators, load timeline
                    # if not set_full: load timeline
                    # todo: implement set_full
                    logger.debug(f"api: set_timeline with {index=} and {set_full=}")
                    self.patternscheduler.load_timeline_from_index(int(index))
                case {"action": "clear_effect_queue"}:
                    self.effecthandler.clear_qeueues()
                    logger.debug("api: cleared all effect queues")
                case {"action": "set_effect", **other_kwargs}:
                    logger.debug(f"api: set_effect: {other_kwargs}")
                    self.effecthandler.load_effect(**other_kwargs)
                case {
                    "action": "modify_effect",
                    "operation": operation,
                    "effect_name": effect_name,
                    "timeline_level": timeline_level,
                }:
                    assert isinstance(effect_name, str)
                    assert isinstance(timeline_level, int)
                    match operation:
                        case "change_draw":
                            logger.debug(f"api: modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_change_draw(effect=effect_name, timeline_level=timeline_level)
                        case "renew_trigger":
                            logger.debug(f"api: modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_renew_trigger(effect=effect_name, timeline_level=timeline_level)
                        case "alternate":
                            logger.debug(f"api: modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_alternate(effect=effect_name, timeline_level=timeline_level)
                        case "remove":
                            logger.debug(f"api: modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_remove(effect=effect_name, timeline_level=timeline_level)
                        case _:
                            logger.warning(
                                f"api: instruction with 'action': 'modify_effect' and {operation=} not understood"
                            )
                case {
                    "action": "set_color",
                    "color_rgb": color_rgb,
                    "color_key": color_key,
                }:
                    self.settings.color_engine.set_color_with_rule(color=color_rgb, color_key=color_key)

                case other:
                    logger.error(f"api: instruction not understood: {other=}")
