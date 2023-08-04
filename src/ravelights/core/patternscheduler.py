import logging
import random
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Iterable, Type, cast

from ravelights.configs.components import (
    BlueprintPlace,
    BlueprintSel,
    Keywords,
    blueprint_effects,
    blueprint_generators,
    blueprint_timelines,
    create_from_blueprint,
)
from ravelights.core.device import Device
from ravelights.core.effecthandler import EffectHandler
from ravelights.core.generator_super import Dimmer, Generator, Pattern, Thinner, Vfilter
from ravelights.core.instruction import InstructionDevice, InstructionEffect
from ravelights.core.settings import Settings
from ravelights.core.templateobjects import EffectSelectorPlacing, GenPlacing, GenSelector
from ravelights.core.timehandler import TimeHandler
from ravelights.core.utils import p
from ravelights.effects.effect_super import Effect

if TYPE_CHECKING:
    from ravelights.app import RaveLightsApp


logger = logging.getLogger(__name__)


# todo: this should not be dataclass
@dataclass
class PatternScheduler:
    root: "RaveLightsApp"
    settings: Settings = field(init=False)
    timehandler: TimeHandler = field(init=False)
    effecthandler: EffectHandler = field(init=False)
    devices: list[Device] = field(init=False)

    def __post_init__(self) -> None:
        self.settings = self.root.settings
        self.timehandler = self.root.settings.timehandler
        self.effecthandler = self.root.effecthandler
        self.devices: list[Device] = self.root.devices

        self.timeline_selectors: list[GenSelector] = []

        # ─── GENERATORS ──────────────────────────────────────────────────
        self.blueprint_timelines = blueprint_timelines
        for device in self.devices:
            kwargs = dict(root=self.root, device=device)
            generators = create_from_blueprint(blueprints=blueprint_generators, kwargs=kwargs)
            device.rendermodule.register_generators(generators=generators)
        self.settings.meta["available_timelines"] = self.get_meta_available_timelines()
        self.settings.meta["available_keywords"] = self.get_meta_available_keywords()
        self.settings.meta["available_generators"] = self.get_meta_available_generators()
        self.load_timeline_from_index(self.settings.active_timeline_index)

    def get_meta_available_timelines(self) -> list[str]:
        blueprint_timelines = cast(Iterable[dict[str, dict[str, str]]], self.blueprint_timelines)
        timeline_names: list[str] = [blue["meta"]["name"] for blue in blueprint_timelines]
        return timeline_names

    def get_meta_available_keywords(self) -> list[str]:
        available_keywords: set[str] = set()
        for item in blueprint_generators + blueprint_effects:
            if "keywords" in item.args:
                keywords: list[Keywords] = cast(list[Keywords], item.args["keywords"])
                for keyword in keywords:
                    available_keywords.add(keyword.value)
        return list(available_keywords)

    def get_meta_available_generators(self) -> dict[str, list[dict[str, str | list[str] | float]]]:
        """Creates a dictionary containing all available Effects, Vfilters, Dimmers, Thinners and GlobalEffects

        Structure is as follows
        {
            "pattern": [
                {
                    "generator_name": "p_foo",
                    "generator_keywords": ["key1", "key2", "key3"],
                    "generator_weight": 0.5,
                },
                {
                    "generator_name": "p_bar",
                    "generator_keywords": ["key1"],
                    "generator_weight": 1.5,
                },
            "vfilter": [
                {
                    "generator_name": "v_foo",
                    "generator_keywords": [],
                    "generator_weight": 1.0,
                },
            ]
        }"""

        keys = self.settings.generator_classes_identifiers
        meta_available_generators: dict[str, list[dict[str, str | list[str] | float]]] = {key: [] for key in keys}
        for item in blueprint_generators + blueprint_effects:
            cls = cast(Type[Generator | Effect], item.cls)
            class_identifier = cls.get_identifier()
            generator_name: str = cast(str, item.args["name"])
            generator_keywords_obj: list[Keywords] = cast(list[Keywords], item.args.get("keywords", []))
            generator_keywords: list[str] = [p.value for p in generator_keywords_obj]
            generator_weight: float = float(cast(float | int, item.args.get("weight", 1.0)))
            new_dict: dict[str, str | list[str] | float] = {
                "generator_name": generator_name,
                "generator_keywords": generator_keywords,
                "generator_weight": generator_weight,
            }
            meta_available_generators[class_identifier].append(new_dict)
        return meta_available_generators

    def load_timeline_from_index(self, index: int):
        self.settings.active_timeline_index = index
        self.load_timeline(self.blueprint_timelines[index])

    def load_timeline(self, timeline: dict[str, dict[str, str] | list[BlueprintSel] | list[BlueprintPlace]]):
        self.clear_instruction_queues()

        blueprints_selectors: list[BlueprintSel] = cast(list[BlueprintSel], timeline["selectors"])
        kwargs = dict(patternscheduler=self)
        self.timeline_selectors: list[GenSelector] = create_from_blueprint(blueprints=blueprints_selectors, kwargs=kwargs)
        self.process_timeline_selectors()

        blueprints_placements: list[BlueprintPlace] = cast(list[BlueprintPlace], timeline["placements"])
        self.process_timeline_placements(blueprints_placements)

    def process_timeline_selectors(self):
        self.settings.clear_selected()  # todo: should this happen?
        for selector in self.timeline_selectors:
            if not p(selector.p):
                continue
            self.process_selector_object(selector)

    def process_timeline_placements(self, blueprints_placements: list[BlueprintPlace]):
        kwargs = dict(patternscheduler=self)
        placements = create_from_blueprint(blueprints=blueprints_placements, kwargs=kwargs)
        for placement in placements:
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
        if obj.pattern_name:
            self.settings.set_generator(gen_type=Pattern, level_index=obj.level, gen_name=obj.pattern_name)
            if self.settings.settings_autopilot["autoload_triggers"]:
                self.load_generator_specific_trigger(gen_name=obj.pattern_name, level=obj.level)

        if obj.vfilter_name:
            self.settings.set_generator(gen_type=Vfilter, level_index=obj.level, gen_name=obj.vfilter_name)
            if self.settings.settings_autopilot["autoload_triggers"]:
                self.load_generator_specific_trigger(gen_name=obj.pattern_name, level=obj.level)

        if obj.dimmer_name:
            self.settings.set_generator(gen_type=Dimmer, level_index=obj.level, gen_name=obj.dimmer_name)
            if self.settings.settings_autopilot["autoload_triggers"]:
                self.load_generator_specific_trigger(gen_name=obj.pattern_name, level=obj.level)

        if obj.thinner_name:
            self.settings.set_generator(gen_type=Thinner, level_index=obj.level, gen_name=obj.thinner_name)
            if self.settings.settings_autopilot["autoload_triggers"]:
                self.load_generator_specific_trigger(gen_name=obj.pattern_name, level=obj.level)

    def load_generator_specific_trigger(self, gen_name: str, level: int):
        generator = self.devices[0].rendermodule.get_generator_by_name(gen_name)
        trigger = random.choice(generator.possible_triggers)
        kwargs = asdict(trigger)
        self.settings.set_trigger(gen_type=generator.get_identifier(), level_index=level, **kwargs)

    def process_generator_placement_object(self, obj: GenPlacing):
        instruction = InstructionDevice(level=obj.level)
        for timing in obj.timings:
            self.send_to_devices(instruction, timing=timing)

    def process_effect_placement_object(self, obj: EffectSelectorPlacing):
        instruction = InstructionEffect(effect_name=obj.effect_name, effect_length_frames=obj.effect_length_frames)
        for timing in obj.timings:
            self.send_to_effect(instruction, timing=timing)

    def send_to_devices(self, ins: InstructionDevice, timing: int) -> None:
        for device in self.devices:
            device.instructionhandler.instruction_queue.add_instruction(ins, n_quarter=timing)

    def send_to_effect(self, ins: InstructionEffect, timing: int) -> None:
        self.effecthandler.instruction_queue.add_instruction(ins, n_quarter=timing)

    def generate_instructions(self):
        pass
