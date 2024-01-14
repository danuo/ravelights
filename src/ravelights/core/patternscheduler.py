from typing import TYPE_CHECKING, cast

from loguru import logger  # type:ignore
from ravelights.configs.components import (
    BlueprintPlace,
    BlueprintSel,
    BlueprintTimeline,
    blueprint_generators,
    blueprint_timelines,
    create_from_blueprint,
)
from ravelights.core.device import Device
from ravelights.core.effecthandler import EffectHandler
from ravelights.core.generator_super import Dimmer, Pattern, Thinner, Vfilter
from ravelights.core.instruction import InstructionDevice, InstructionEffect
from ravelights.core.settings import Settings
from ravelights.core.templateobjects import EffectSelectorPlacing, GenPlacing, GenSelector
from ravelights.core.timehandler import TimeHandler
from ravelights.core.utils import p

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


class PatternScheduler:
    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings: Settings = self.root.settings
        self.timehandler: TimeHandler = self.root.timehandler
        self.effecthandler: EffectHandler = self.root.effecthandler
        self.devices: list[Device] = self.root.devices
        self.timeline_selectors: list[GenSelector] = []
        self.timeline_placements: list[BlueprintPlace] = []

        # ─── GENERATORS ──────────────────────────────────────────────────
        self.blueprint_timelines = blueprint_timelines
        for device in self.devices:
            kwargs = dict(root=self.root, device=device)
            generators = create_from_blueprint(blueprints=blueprint_generators, kwargs=kwargs)
            device.rendermodule.register_generators(generators=generators)

        self.load_timeline_from_index(self.settings.active_timeline_index)

    def load_timeline_from_index(self, index: int):
        self.settings.active_timeline_index = index
        self.load_timeline(self.blueprint_timelines[index])

    def load_timeline(self, timeline: BlueprintTimeline):
        self.clear_instruction_queues()

        blueprints_selectors: list[BlueprintSel] = cast(list[BlueprintSel], timeline["selectors"])
        kwargs = dict(root=self.root)
        self.timeline_selectors: list[GenSelector] = create_from_blueprint(
            blueprints=blueprints_selectors, kwargs=kwargs
        )
        self.process_timeline_selectors()

        blueprints_placements: list[BlueprintPlace] = cast(list[BlueprintPlace], timeline["placements"])
        kwargs = dict(root=self.root)
        self.timeline_placements = create_from_blueprint(blueprints=blueprints_placements, kwargs=kwargs)
        self.process_timeline_placements()

    def process_timeline_selectors(self):
        self.settings.clear_selected()  # todo: should this happen?
        for selector in self.timeline_selectors:
            if not p(selector.p):
                continue
            self.process_selector_object(selector)

    def process_timeline_placements(self):
        for placement in self.timeline_placements:
            if not p(placement.p):
                continue
            if isinstance(placement, GenPlacing):
                self.process_generator_placement_object(placement)
            if isinstance(placement, EffectSelectorPlacing):
                self.process_effect_placement_object(placement)

    def clear_instruction_queues(self):
        """Clears queues for global effects, device effects and instructions"""
        for device in self.devices:
            device.instructionhandler.instruction_queue.clear()
        self.effecthandler.instruction_queue.clear()

    def process_selector_object(self, obj: GenSelector):
        # load each generator that is defined inside of the GenSelector Object
        renew_trigger = self.settings.renew_trigger_from_timeline
        if obj.pattern_name:
            self.settings.set_generator(
                gen_type=Pattern, timeline_level=obj.level, gen_name=obj.pattern_name, renew_trigger=renew_trigger
            )

        if obj.vfilter_name:
            self.settings.set_generator(
                gen_type=Vfilter, timeline_level=obj.level, gen_name=obj.vfilter_name, renew_trigger=renew_trigger
            )

        if obj.dimmer_name:
            self.settings.set_generator(
                gen_type=Dimmer, timeline_level=obj.level, gen_name=obj.dimmer_name, renew_trigger=renew_trigger
            )

        if obj.thinner_name:
            self.settings.set_generator(
                gen_type=Thinner, timeline_level=obj.level, gen_name=obj.thinner_name, renew_trigger=renew_trigger
            )

    def process_generator_placement_object(self, obj: GenPlacing):
        instruction = InstructionDevice(level=obj.level)
        for timing in obj.timings:
            self.send_to_devices(instruction, timing=timing)

    def process_effect_placement_object(self, obj: EffectSelectorPlacing):
        instruction = InstructionEffect(effect_name=obj.effect_name, effect_length_frames=obj.effect_length_frames)
        for timing in obj.timings:
            self.send_to_effect(instruction, timing=timing)

    def send_to_devices(self, ins: InstructionDevice, timing: int):
        for device in self.devices:
            device.instructionhandler.instruction_queue.add_instruction(ins, n_quarter=timing)

    def send_to_effect(self, ins: InstructionEffect, timing: int):
        self.effecthandler.instruction_queue.add_instruction(ins, n_quarter=timing)

    def generate_instructions(self):
        pass
