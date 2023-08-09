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
                    if level == 0:  # level = 0 means auto
                        level = self.patternscheduler.devices[0].rendermodule.device_timeline_level
                    generator = self.patternscheduler.devices[0].rendermodule.get_selected_generator(gen_type=gen_type, level=level)
                    self.patternscheduler.load_generator_specific_trigger(gen_name=generator.name, level=level)
                case {"action": "gen_command", "gen_type": gen_type, "level": level, "command": command}:
                    if level == 0:
                        level = None  # auto mode
                    for dev in self.patternscheduler.devices:
                        generator = dev.rendermodule.get_selected_generator(gen_type=gen_type, level=level)
                        function = getattr(generator, command)
                        function()
                case {"action": "change_settings", "selectedColorSpeed": speed_str}:
                    assert False
                    self.settings.color_engine.set_color_speed(speed_str)
                case {"action": "change_settings", **other_kwargs}:
                    print(other_kwargs)
                    self.settings.update_from_dict(other_kwargs)
                case {"action": "set_trigger", **other_kwargs}:
                    self.settings.set_trigger(**other_kwargs)
                case {"action": "set_generator", **other_kwargs}:
                    self.settings.set_generator(**other_kwargs)
                case {"action": "set_timeline", "timeline_index": index, "set_full": set_full}:
                    print(index, set_full)
                    # todo: implement set_full
                    self.patternscheduler.load_timeline_from_index(int(index))
                case {"action": "generator_alternate"}:
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
