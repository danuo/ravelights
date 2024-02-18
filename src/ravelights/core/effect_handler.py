from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Optional

from loguru import logger
from ravelights.configs.components import blueprint_effects, blueprint_generators
from ravelights.core.generator_super import Vfilter
from ravelights.core.instruction import InstructionEffect
from ravelights.core.instruction_queue import InstructionQueue
from ravelights.core.settings import Settings
from ravelights.core.time_handler import TimeHandler
from ravelights.effects.effect_super import Effect, EffectWrapper
from ravelights.effects.special_effect_vfilter import SpecialEffectVfilter

if TYPE_CHECKING:
    from ravelights.core.device import Device
    from ravelights.core.ravelights_app import RaveLightsApp


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

    def __post_init__(self) -> None:
        self.settings = self.root.settings
        self.timehandler = self.root.time_handler
        self.devices: list[Device] = self.root.devices
        self.instruction_queue = InstructionQueue(root=self.root)
        self.effect_wrappers_dict: dict[str, EffectWrapper] = dict()
        self.build_effectwrappers_from_blueprints()
        self.build_effectwrappers_from_vfilters()

    def build_effectwrappers_from_blueprints(self) -> None:
        effects_per_device: list[list[Effect]] = []
        for device in self.devices:
            kwargs = dict(root=self.root, device=device)
            effects: list[Effect] = [blueprint.create_instance(kwargs) for blueprint in blueprint_effects]
            effects_per_device.append(effects)
        for effect_objects in zip(*effects_per_device):
            effect_wrapper = EffectWrapper(root=self.root, effect_objects=effect_objects)
            self.effect_wrappers_dict[effect_wrapper.name] = effect_wrapper

    def build_effectwrappers_from_vfilters(self) -> None:
        for blueprint in blueprint_generators:
            if not issubclass(blueprint.cls, Vfilter) or "none" in blueprint.name:
                continue
            vfilter_name: str = blueprint.name
            effect_name = "e" + vfilter_name
            effects: list[Effect] = []
            for device in self.devices:
                effect = SpecialEffectVfilter(root=self.root, device=device, name=effect_name, vfilter=blueprint.cls)
                effects.append(effect)
            effect_wrapper = EffectWrapper(root=self.root, effect_objects=effects)
            self.effect_wrappers_dict[effect_wrapper.name] = effect_wrapper

    def run_before(self) -> None:
        self.load_and_apply_instructions()

        # ---------------------------------- remove ---------------------------------- #
        for effect_wrapper in self.effect_queue:
            if effect_wrapper.is_finished():
                effect_wrapper.on_delete()
                self.effect_queue.remove(effect_wrapper)

        # ─── Assemble Queues ──────────────────────────────────────────
        for effect_wrapper in self.effect_queue:
            # ---------------------------------- trigger --------------------------------- #
            if effect_wrapper.trigger:
                if effect_wrapper.trigger.is_match(self.timehandler.beat_state):
                    effect_wrapper.on_trigger()
            # ----------------------------------- sync ----------------------------------- #
            effect_wrapper.sync_effects()

            # ------------------------------ counting before ----------------------------- #
            effect_wrapper.counting_before_check()

            # ------------------------------- check active ------------------------------- #
            effect_wrapper.active = effect_wrapper.check_active()

            # ------------------------------ counting after ------------------------------ #
            effect_wrapper.counting_after_check()

            # -------------------------------- run before -------------------------------- #
            effect_wrapper.run_before()

    def run_after(self) -> None:
        for effect_wrapper in self.effect_queue:
            effect_wrapper.run_after()

    def clear_qeueues(self) -> None:
        self.effect_queue.clear()
        self.instruction_queue.clear()

    def load_and_apply_instructions(self) -> None:  # before
        instructions_for_frame = self.instruction_queue.get_instructions()
        for ins in instructions_for_frame:
            self.apply_effect_instruction(ins)

    def apply_effect_instruction(self, instruction: InstructionEffect) -> None:
        # todo: this is not implemented
        assert False
        effect_name = instruction.effect_name
        if effect_name is None:
            logger.debug("todo: implement")
        length_frames = instruction.effect_length_frames
        self.load_effect(effect_name=effect_name, length_frames=length_frames)

    def load_effect(
        self,
        effect_name: str,
        mode: Literal["frames"],
        **kwargs: dict[str, Optional[Any]],
    ) -> None:
        assert mode in ("frames",)

        logger.info(f"setting {effect_name} with {kwargs}")
        effect_wrapper: EffectWrapper = self.find_effect(name=effect_name)
        if mode == "frames":
            assert "limit_frames" in kwargs
            effect_wrapper.reset_frames(**kwargs)  # type: ignore

        else:
            effect_wrapper.reset(**kwargs)  # type: ignore

        logger.debug(self.effect_queue)
        self.effect_queue.append(effect_wrapper)
        logger.debug(self.effect_queue)
        self.root.refresh_ui(sse_event="effect")

    def effect_renew_trigger(self, effect: str | EffectWrapper) -> None:
        if isinstance(effect, str):
            effect = self.find_effect(name=effect)
        assert isinstance(effect, EffectWrapper)
        if effect in self.effect_queue:
            effect.renew_trigger()

    def effect_alternate(self, effect: str | EffectWrapper) -> None:
        if isinstance(effect, str):
            effect = self.find_effect(name=effect)
        assert isinstance(effect, EffectWrapper)
        if effect in self.effect_queue:
            effect.alternate()

    def effect_remove(self, effect: str | EffectWrapper) -> None:
        if isinstance(effect, str):
            effect = self.find_effect(name=effect)
        assert isinstance(effect, EffectWrapper)
        if effect in self.effect_queue:
            effect.on_delete()
            self.effect_queue.remove(effect)

    def find_effect(self, name: str) -> EffectWrapper:
        return self.effect_wrappers_dict[name]
