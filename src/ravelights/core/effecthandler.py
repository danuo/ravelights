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
        self.effect_wrappers_dict: dict[str, EffectWrapper] = dict()
        device_ids = []
        effects_per_device: list[list[Effect]] = []
        for device in self.devices:
            device_ids.append(device.device_id)
            kwargs = dict(root=self.root, device=device)
            effects: list[Effect] = create_from_blueprint(blueprints=blueprint_effects, kwargs=kwargs)
            effects_per_device.append(effects)
        for effect_objects in zip(*effects_per_device):
            effect_wrapper = EffectWrapper(root=self.root, effect_objects=effect_objects, device_ids=device_ids)
            self.effect_wrappers_dict[effect_wrapper.name] = effect_wrapper

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
                self.effect_queue.remove(item)

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
        self.effect_queue.append(effect_wrapper)

    def remove_effect(self, effect: str | EffectWrapper):
        if isinstance(effect, str):
            effect = self.find_effect(name=effect)
        assert isinstance(effect, EffectWrapper)
        if effect in self.effect_queue:
            effect.on_delete()
            self.effect_queue.remove(effect)

    def find_effect(self, name: str) -> EffectWrapper:
        return self.effect_wrappers_dict[name]

    def do_counting(self):
        for effect_wrapper in self.effect_queue:
            effect_wrapper.perform_counting_per_frame()
