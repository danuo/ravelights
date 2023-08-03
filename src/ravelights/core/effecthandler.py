import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Type

from ravelights.configs.components import blueprint_effects, create_from_blueprint
from ravelights.core.instruction import InstructionEffect
from ravelights.core.instructionqueue import InstructionQueue
from ravelights.core.settings import Settings
from ravelights.core.timehandler import TimeHandler
from ravelights.effects.effect_super import Effect, EffectWrapper

if TYPE_CHECKING:
    from ravelights.app import RaveLightsApp
    from ravelights.core.device import Device

logger = logging.getLogger(__name__)


@dataclass
class EffectHandler:
    """
    effect_queue: queue for Effect objects. They get removed once length_frames limit is reached
    instruction_queue: queue for InstructionEffect objects
    """

    root: "RaveLightsApp"
    devices: list["Device"] = field(init=False)
    settings: "Settings" = field(init=False)
    timehandler: "TimeHandler" = field(init=False)
    instruction_queue: InstructionQueue = field(init=False)
    effect_queue: list[EffectWrapper] = field(default_factory=list)

    def __post_init__(self):
        self.settings = self.root.settings
        self.timehandler = self.root.settings.timehandler
        self.devices: list[Device] = self.root.devices
        self.instruction_queue = InstructionQueue(settings=self.settings)
        device_ids = []
        effects_per_device: list[list[Effect]] = []
        for device in self.devices:
            device_ids.append(device.device_id)
            kwargs = dict(root=self.root, device=device)
            effects: list[Effect] = create_from_blueprint(blueprints=blueprint_effects, kwargs=kwargs)
            effects_per_device.append(effects)
        effect_wrappers: list[EffectWrapper] = []
        for effect_objects in zip(*effects_per_device):
            wrapper = EffectWrapper(root=self.root, effect_objects=effect_objects, device_ids=device_ids)
            effect_wrappers.append(wrapper)
        self.register_effects(effect_wrappers=effect_wrappers)

    def clear_qeueues(self):
        self.effect_queue.clear()
        self.instruction_queue.clear()

    def load_and_apply_instructions(self):  # before
        # ─── LOAD INSTRUCTIONS ───────────────────────────────────────────
        instructions_for_frame = self.instruction_queue.get_instructions()
        for ins in instructions_for_frame:
            self.apply_effect_instruction(ins)
        for item in self.effect_queue:
            if item.is_finished():
                self.remove_item(item)

    def apply_effect_instruction(self, instruction: InstructionEffect):
        effect_name = instruction.effect_name
        if effect_name is None:
            assert False
        length_frames = instruction.effect_length_frames
        self.load_effect(effect_name=effect_name, length_frames=length_frames)

    def load_effect(self, effect_name: str, **kwargs):
        print("in EffectHandler", effect_name, kwargs)
        effect_wrapper: EffectWrapper = self.find_effect(name=effect_name)
        effect_wrapper.reset(**kwargs)
        self.add_item(effect_wrapper)

    def add_item(self, item: EffectWrapper):
        self.effect_queue.append(item)

    def remove_item(self, item: EffectWrapper):
        item.on_delete()
        self.effect_queue.remove(item)

    def register_effects(self, effect_wrappers: list[EffectWrapper]):
        self.effect_wrappers_dict: dict[str, EffectWrapper] = dict()
        for effect_wrapper in effect_wrappers:
            self.effect_wrappers_dict.update({effect_wrapper.name: effect_wrapper})

    def find_effect(self, name: str) -> EffectWrapper:
        return self.effect_wrappers_dict[name]
