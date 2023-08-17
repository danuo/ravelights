import logging
from typing import TYPE_CHECKING

from ravelights.core.custom_typing import T_JSON
from ravelights.core.effecthandler import EffectHandler
from ravelights.core.patternscheduler import PatternScheduler
from ravelights.core.settings import Settings

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
        self.modification_queue: list[T_JSON] = []

    def add_to_modification_queue(self, receive_data: T_JSON) -> None:
        """Queue incomming api calls here to be processed later at the beginning of a frame cycle."""
        self.modification_queue.append(receive_data)

    def apply_settings_modifications_queue(self) -> None:
        while self.modification_queue:
            receive_data: T_JSON = self.modification_queue.pop()
            match receive_data:
                case {"action": "gen_command", "gen_type": gen_type, "timeline_level": timeline_level, "command": "renew_trigger"}:
                    logger.info(f"gen_command with {gen_type} at level {timeline_level} and command renew_trigger")
                    device = self.patternscheduler.devices[0]
                    if timeline_level == 0:  # level = 0 means auto
                        timeline_level = device.rendermodule.get_timeline_level()
                    self.settings.renew_trigger(gen_type=gen_type, timeline_level=timeline_level)
                case {"action": "gen_command", "gen_type": gen_type, "timeline_level": timeline_level, "command": command}:
                    logger.info(f"gen_command with {gen_type} at level {timeline_level} and command {command}")
                    for device in self.patternscheduler.devices:
                        if timeline_level == 0:
                            timeline_level = device.rendermodule.get_timeline_level()
                        generator = device.rendermodule.get_selected_generator(gen_type=gen_type, timeline_level=timeline_level)
                        function = getattr(generator, command)
                        function()
                case {"action": "set_sync"}:
                    self.settings.bpmhandler.bpm_sync()
                case {"action": "adjust_sync", "value": value}:
                    assert isinstance(value, float)
                    self.settings.timehandler.time_sync += value
                case {"action": "set_settings", "color_transition_speed": speed_str}:
                    logger.info(f"set_settings color_transition_speed {speed_str}")
                    assert isinstance(speed_str, str)
                    self.settings.color_transition_speed = speed_str
                    self.settings.color_engine.set_color_speed(speed_str)
                case {"action": "set_settings", **other_kwargs}:
                    logger.info(f"set_settings {other_kwargs}")
                    self.settings.update_from_dict(other_kwargs)
                case {"action": "set_settings_autopilot", **other_kwargs}:
                    logger.info("set_settings_autopilot (...)")
                    self.settings.settings_autopilot.update(other_kwargs)
                case {"action": "set_device_settings", "device_id": device_id, **other_kwargs}:
                    assert isinstance(device_id, int)
                    self.devices[device_id].update_from_dict(other_kwargs)
                case {"action": "set_trigger", **other_kwargs}:
                    self.settings.set_trigger(**other_kwargs)
                case {"action": "set_generator", **other_kwargs}:
                    renew_trigger = self.settings.renew_trigger_from_manual
                    self.settings.set_generator(renew_trigger=renew_trigger, **other_kwargs)
                case {"action": "set_timeline", "timeline_index": index, "set_full": set_full}:
                    # if set_full:     load generators, load timeline
                    # if not set_full: load timeline
                    print(index, set_full)
                    # todo: implement set_full
                    self.patternscheduler.load_timeline_from_index(int(index))
                case {"action": "generator_alternate"}:
                    print("todo: implement")
                    # todo: implement
                    pass
                    # self.patternscheduler.alternate_timeline(**receive_data)
                case {"action": "generator_beat"}:
                    pass
                case {"action": "clear_effect_queue"}:
                    self.effecthandler.clear_qeueues()
                    logger.info("cleared all effect queues")
                case {"action": "set_effect", **other_kwargs}:
                    logger.info(f"set_effect: {other_kwargs}")
                    self.effecthandler.load_effect(**other_kwargs)
                case {"action": "modify_effect", "operation": operation, "effect_name": effect_name}:
                    assert isinstance(effect_name, str)
                    match operation:
                        case "renew_trigger":
                            logger.info(f"modify_effect renew_trigger: {effect_name}")
                            self.effecthandler.effect_renew_trigger(effect=effect_name)
                        case "alternate":
                            logger.info(f"modify_effect alter: {effect_name}")
                            self.effecthandler.effect_alternate(effect=effect_name)
                        case "remove":
                            logger.info(f"modify_effect remove: {effect_name}")
                            self.effecthandler.effect_remove(effect=effect_name)
                case other:
                    logger.warning(other)
                    logger.warning("API instruction not understood")
