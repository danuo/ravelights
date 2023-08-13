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
                case {"action": "gen_command", "gen_type": gen_type, "level": level, "command": "new trigger"}:
                    device = self.patternscheduler.devices[0]
                    if level == 0:  # level = 0 means auto
                        level = device.rendermodule.device_timeline_level
                    generator = device.rendermodule.get_selected_generator(gen_type=gen_type, timeline_level=level)
                    self.patternscheduler.load_generator_specific_trigger(gen_name=generator.name, timeline_level=level)
                case {"action": "gen_command", "gen_type": gen_type, "level": level, "command": command}:
                    if level == 0:
                        level = None  # auto mode
                    for device in self.patternscheduler.devices:
                        generator = device.rendermodule.get_selected_generator(gen_type=gen_type, timeline_level=level)
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
                    self.settings.set_generator(**other_kwargs)
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
                    print("cleared all effect queues")
                case {"action": "set_effect", **other_kwargs}:
                    print("in EventHandler", other_kwargs)
                    self.effecthandler.load_effect(**other_kwargs)
                case {"action": "remove_effect", "effect_name": effect_name}:
                    print("remove_effect: ", effect_name)
                    self.effecthandler.remove_effect(effect=effect_name)
                case other:
                    logger.warning(other)
                    logger.warning("API instruction not understood")
