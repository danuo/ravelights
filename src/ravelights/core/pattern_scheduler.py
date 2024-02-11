from typing import TYPE_CHECKING

from loguru import logger
from ravelights.configs.components import (
    Timeline,
    blueprint_generators,
    blueprint_timelines,
)
from ravelights.core.device import Device
from ravelights.core.effect_handler import EffectHandler
from ravelights.core.generator_super import Dimmer, Pattern, Thinner, Vfilter
from ravelights.core.instruction import InstructionDevice, InstructionEffect
from ravelights.core.settings import Settings
from ravelights.core.time_handler import TimeHandler
from ravelights.core.timeline import EffectSelectorPlacing, GeneratorSet, GenPlacing, GenSelector
from ravelights.core.utils import p

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


class PatternScheduler:
    def __init__(self, root: "RaveLightsApp") -> None:
        self.root = root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.root.time_handler
        self.effecthandler: EffectHandler = self.root.effect_handler
        self.devices: list[Device] = self.root.devices
        self.timeline_selectors: list[GenSelector] = []
        self.timeline_placements: list[GenPlacing] = []

        # ─── GENERATORS ──────────────────────────────────────────────────
        self.blueprint_timelines = blueprint_timelines
        for device in self.devices:
            kwargs = dict(root=self.root, device=device)
            generators: list[Pattern | Vfilter | Dimmer | Thinner] = [
                blueprint.create_instance(kwargs) for blueprint in blueprint_generators
            ]
            device.rendermodule.register_generators(generators=generators)

    def load_timeline_from_index(self, index: int) -> None:
        self.settings.active_timeline_index = index
        self._load_timeline(self.blueprint_timelines[index])

    def load_timeline_by_name(self, name: str) -> None:
        for index, timeline in enumerate(self.blueprint_timelines):
            if timeline["meta"]["name"] == name:
                self.settings.active_timeline_index = index
                self._load_timeline(self.blueprint_timelines[index])
                logger.debug(f"loading timeline {name} at index {index}")
                return
        logger.warning(f"could not find timeline with name {name}")

    def _load_timeline(self, timeline: Timeline) -> None:
        self.settings.reset_selected()
        self.clear_instruction_queues()

        self.timeline_selectors = timeline["selectors"]
        for selector in self.timeline_selectors:
            selector.set_root(self.root)
        self.process_timeline_selectors(self.timeline_selectors)

        self.timeline_placements = timeline["placements"]
        self.process_timeline_placements(self.timeline_placements)

    def process_timeline_selectors(self, timeline_selectors: list[GenSelector]) -> None:
        for selector in timeline_selectors:
            if not p(selector.p):
                continue
            self.process_generator_selector(selector)

    def process_generator_selector(self, generator_selector: GenSelector) -> None:
        # load each generator that is defined inside of the GenSelector Object
        renew_trigger = self.settings.renew_trigger_from_timeline

        for device_index, device in enumerate(self.devices):
            if not device.refresh_generators_from_timeline:
                continue

            if isinstance(device.linked_to, int):
                continue

            genset: GeneratorSet = generator_selector.create_generator_set()
            assert 1 <= generator_selector.level <= 3
            if genset.pattern_name:
                self.settings.set_generator(
                    device_index=device_index,
                    gen_type="pattern",
                    timeline_level=generator_selector.level,
                    gen_name=genset.pattern_name,
                    renew_trigger=renew_trigger,
                )

            if genset.vfilter_name:
                self.settings.set_generator(
                    device_index=device_index,
                    gen_type="vfilter",
                    timeline_level=generator_selector.level,
                    gen_name=genset.vfilter_name,
                    renew_trigger=renew_trigger,
                )

            if genset.dimmer_name:
                self.settings.set_generator(
                    device_index=device_index,
                    gen_type="dimmer",
                    timeline_level=generator_selector.level,
                    gen_name=genset.dimmer_name,
                    renew_trigger=renew_trigger,
                )

            if genset.thinner_name:
                self.settings.set_generator(
                    device_index=device_index,
                    gen_type="thinner",
                    timeline_level=generator_selector.level,
                    gen_name=genset.thinner_name,
                    renew_trigger=renew_trigger,
                )

    def process_timeline_placements(self, timeline_placements: list[GenPlacing]) -> None:
        for placement in timeline_placements:
            if not p(placement.p):
                continue
            if isinstance(placement, GenPlacing):
                self.process_generator_placement_object(placement)
            if isinstance(placement, EffectSelectorPlacing):
                self.process_effect_placement_object(placement)

    def clear_instruction_queues(self) -> None:
        """Clears queues for global effects, device effects and instructions"""
        for device in self.devices:
            device.instructionhandler.instruction_queue.clear()
        self.effecthandler.instruction_queue.clear()

    def process_generator_placement_object(self, obj: GenPlacing) -> None:
        instruction = InstructionDevice(level=obj.level)
        for timing in obj.timings:
            self.send_to_devices(instruction, timing=timing)

    def process_effect_placement_object(self, obj: EffectSelectorPlacing) -> None:
        instruction = InstructionEffect(effect_name=obj.effect_name, effect_length_frames=obj.effect_length_frames)
        for timing in obj.timings:
            self.send_to_effect(instruction, timing=timing)

    def send_to_devices(self, ins: InstructionDevice, timing: int) -> None:
        for device in self.devices:
            device.instructionhandler.instruction_queue.add_instruction(ins, n_quarter=timing)

    def send_to_effect(self, ins: InstructionEffect, timing: int) -> None:
        self.effecthandler.instruction_queue.add_instruction(ins, n_quarter=timing)

    def generate_instructions(self) -> None:
        logger.warning("function undefined")
        pass

    # def get_effective_device_index(self) -> int:
    # this doesnt make sense. if device_index = None -> apply to all

    def get_effective_timeline_level(self, device_index: int) -> int:
        return self.devices[device_index].get_effective_timeline_level()
