import logging
from typing import TYPE_CHECKING, Any

from ravelights.core.effecthandler import EffectHandler
from ravelights.core.patternscheduler import PatternScheduler
from ravelights.core.settings import Settings, get_default_color_mappings

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings: Settings = self.root.settings
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
                    "gen_type": gen_type,
                    "timeline_level": timeline_level,
                    "command": "renew_trigger",
                }:
                    logger.info(f"gen_command with {gen_type} at level {timeline_level} and command renew_trigger")
                    device = self.patternscheduler.devices[0]
                    if timeline_level == 0:  # level = 0 means auto
                        timeline_level = device.rendermodule.get_timeline_level()
                    self.settings.renew_trigger(gen_type=gen_type, timeline_level=timeline_level)
                case {
                    "action": "gen_command",
                    "gen_type": gen_type,
                    "timeline_level": timeline_level,
                    "command": command,
                }:
                    logger.info(f"gen_command with {gen_type} at level {timeline_level} and command {command}")
                    for device in self.patternscheduler.devices:
                        if timeline_level == 0:
                            timeline_level = device.rendermodule.get_timeline_level()
                        generator = device.rendermodule.get_selected_generator(
                            gen_type=gen_type, timeline_level=timeline_level
                        )
                        function = getattr(generator, command)
                        function()
                case {"action": "set_sync"}:
                    self.settings.bpmhandler.bpm_sync()
                case {"action": "adjust_sync", "value": value}:
                    assert isinstance(value, float)
                    self.settings.timehandler.time_sync += value
                case {"action": "reset_color_mappings"}:
                    self.settings.reset_color_mapping()
                case {"action": "set_settings", "color_transition_speed": speed_str}:
                    logger.info(f"set_settings color_transition_speed {speed_str}")
                    if isinstance(speed_str, str):
                        self.settings.set_color_transition_speed(speed_str)
                    else:
                        logger.error("could not apply color_transition_speed, value is not a string")
                case {"action": "set_settings", **other_kwargs}:
                    logger.info(f"set_settings {other_kwargs}")
                    self.settings.update_from_dict(other_kwargs)
                case {"action": "set_settings_autopilot", **other_kwargs}:
                    logger.info("set_settings_autopilot (...)")
                    self.settings.set_settings_autopilot(other_kwargs)
                case {"action": "set_device_settings", "device_id": device_id, **other_kwargs}:
                    assert isinstance(device_id, int)
                    self.devices[device_id].update_from_dict(other_kwargs)
                case {"action": "set_trigger", **other_kwargs}:
                    logger.info(f"set_trigger with {other_kwargs}")
                    self.settings.set_trigger(**other_kwargs)
                case {"action": "set_generator", **other_kwargs}:
                    logger.info(f"set_generator with {other_kwargs}")
                    renew_trigger = self.settings.renew_trigger_from_manual
                    self.settings.set_generator(renew_trigger=renew_trigger, **other_kwargs)
                case {"action": "set_timeline", "timeline_index": index, "set_full": set_full}:
                    # if set_full:     load generators, load timeline
                    # if not set_full: load timeline
                    print(index, set_full)
                    # todo: implement set_full
                    self.patternscheduler.load_timeline_from_index(int(index))
                case {"action": "clear_effect_queue"}:
                    self.effecthandler.clear_qeueues()
                    logger.info("cleared all effect queues")
                case {"action": "set_effect", **other_kwargs}:
                    logger.info(f"set_effect: {other_kwargs}")
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
                            logger.info(f"modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_change_draw(effect=effect_name, timeline_level=timeline_level)
                        case "renew_trigger":
                            logger.info(f"modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_renew_trigger(effect=effect_name, timeline_level=timeline_level)
                        case "alternate":
                            logger.info(f"modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_alternate(effect=effect_name, timeline_level=timeline_level)
                        case "remove":
                            logger.info(f"modify_effect {operation}: {effect_name}")
                            self.effecthandler.effect_remove(effect=effect_name, timeline_level=timeline_level)
                        case _:
                            logger.warning("API instruction with 'action': 'modify_effect' not understood")
                case {
                    "action": "set_color",
                    "color_rgb": color_rgb,
                    "color_key": color_key,
                }:
                    self.settings.color_engine.set_color_with_rule(color=color_rgb, color_key=color_key)

                case other:
                    logger.warning(other)
                    logger.warning("API instruction not understood")
            # self.root.refresh_ui(sse_event="test")
