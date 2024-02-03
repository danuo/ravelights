from typing import TYPE_CHECKING, Sequence

from loguru import logger
from ravelights.configs.components import (
    Timeline,
    blueprint_generators,
    blueprint_timelines,
)
from ravelights.core.device import Device
from ravelights.core.effect_handler import EffectHandler
from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
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
        self.timehandler: TimeHandler = self.root.timehandler
        self.effecthandler: EffectHandler = self.root.effecthandler
        self.devices: list[Device] = self.root.devices
        self.timeline_selectors: list[GenSelector] = []
        self.timeline_placements: list[GenPlacing] = []

        # ─── GENERATORS ──────────────────────────────────────────────────
        self.blueprint_timelines = blueprint_timelines
        for device in self.devices:
            kwargs = dict(root=self.root, device=device)
            generators: Sequence[Generator] = [blueprint.create_instance(kwargs) for blueprint in blueprint_generators]
            device.rendermodule.register_generators(generators=generators)

        self.load_timeline_from_index(self.settings.active_timeline_index)

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
        self.settings.clear_selected()
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

        genset: GeneratorSet = generator_selector.create_generator_set()
        if genset.pattern_name:
            self.settings.set_generator(
                gen_type="pattern",
                timeline_level=generator_selector.level,
                gen_name=genset.pattern_name,
                renew_trigger=renew_trigger,
            )

        if genset.vfilter_name:
            self.settings.set_generator(
                gen_type="vfilter",
                timeline_level=generator_selector.level,
                gen_name=genset.vfilter_name,
                renew_trigger=renew_trigger,
            )

        if genset.dimmer_name:
            self.settings.set_generator(
                gen_type="dimmer",
                timeline_level=generator_selector.level,
                gen_name=genset.dimmer_name,
                renew_trigger=renew_trigger,
            )

        if genset.thinner_name:
            self.settings.set_generator(
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
