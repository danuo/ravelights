from typing import TYPE_CHECKING, Any, NamedTuple

import numpy as np
from flask_restful import fields, marshal
from ravelights.configs.components import Keyword, blueprint_effects, blueprint_generators, blueprint_timelines
from ravelights.core.color_handler import COLOR_TRANSITION_SPEEDS, Color, ColorHandler, SecondaryColorModes
from ravelights.core.controls import CONTROLS_AUDIO, CONTROLS_AUTOPILOT, CONTROLS_GLOBAL_SLIDERS
from ravelights.core.custom_typing import AvailableGenerators, Timeline
from ravelights.core.timeline import GenPlacing

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


class Item(NamedTuple):
    timing: int
    level: int


TIMELINE_COLORS = {
    1: "rgb(113,231,255)",
    2: "rgb(55,30,95)",
    3: "rgb(81,255,0)",
}


class MetaHandler:
    """creates resources that are available via api that are meant to be static during runtime"""

    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings = root.settings
        self.api_content: dict[str, Any] = dict()
        self.api_content["API_VERSION"] = self.root.API_VERSION
        self.api_content["available_timelines"] = self.get_meta_available_timelines()
        self.api_content["available_keywords"] = self.get_meta_available_keywords()
        self.api_content["available_generators"] = self.get_meta_available_generators()
        self.api_content["available_timelines_svg"] = self.get_all_timeline_svgs()  # formerly meta / timelines
        self.api_content["steps_dict"] = self.get_effect_timelines_meta()
        self.api_content["color_transition_speeds"] = [x.value for x in COLOR_TRANSITION_SPEEDS]
        self.api_content["color_sec_mode_names"] = [mode.value for mode in SecondaryColorModes]
        self.api_content["device_meta"] = self.get_device_meta()
        self.api_content["color_palette"] = self.get_color_palette()
        self.api_content["controls_global_sliders"] = CONTROLS_GLOBAL_SLIDERS
        self.api_content["controls_audio"] = CONTROLS_AUDIO
        self.api_content["controls_autopilot"] = CONTROLS_AUTOPILOT

    def __getitem__(self, key: str):
        return self.api_content[key]

    def __setitem__(self, key: str, value: Any):
        self.api_content[key] = value

    def get_meta_available_timelines(self) -> list[str]:
        timeline_names: list[str] = [blue["meta"].name for blue in blueprint_timelines]
        return timeline_names

    def get_meta_available_keywords(self) -> list[str]:
        available_keywords: set[str] = set()
        for item in blueprint_generators + blueprint_effects:
            keywords: list[Keyword] = item.keywords
            for keyword in keywords:
                available_keywords.add(keyword.value)
        return list(available_keywords)

    def get_meta_available_generators(self) -> AvailableGenerators:
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

        meta_available_generators = AvailableGenerators(
            pattern=[],
            vfilter=[],
            thinner=[],
            dimmer=[],
            effect=[],
        )
        generators_and_effects = (
            self.root.devices[0].rendermodule.generators_dict | self.root.effect_handler.effect_wrappers_dict
        )
        for generator_name, gen_cls in generators_and_effects.items():
            class_identifier = gen_cls.identifier
            generator_keywords: list[str] = gen_cls.keywords
            generator_weight: float = gen_cls.weight
            meta_available_generators[class_identifier].append(
                {
                    "generator_name": generator_name,
                    "generator_keywords": generator_keywords,
                    "generator_weight": generator_weight,
                }
            )

        return meta_available_generators

    def get_all_timeline_svgs(self):
        names = []
        descriptions = []
        svgs = []
        colors = [c for c in TIMELINE_COLORS.values()]
        for timeline in blueprint_timelines:
            names.append(timeline["meta"].name)
            descriptions.append(timeline["meta"].description)
            svgs.append(self.get_svg_for_timeline(timeline))
        return dict(names=names, descriptions=descriptions, svgs=svgs, colors=colors)

    def get_svg_for_timeline(self, timeline: Timeline) -> str:
        SVG_HEIGHT = 70

        placements = timeline["placements"]
        items = []
        for placement in placements:
            if not isinstance(placement, GenPlacing):
                continue

            level: int = placement.level
            timings: list[int] = placement.timings
            for timing in timings:
                item = Item(timing, level)
                items.append(item)
        items.append(Item(128, 1))
        items.sort()
        svg_string = f'<svg width="100%" height="100%" viewBox="0 0 128 {SVG_HEIGHT}" preserveAspectRatio="none">\n'
        for i in range(len(items) - 1):
            item_left = items[i]
            item_right = items[i + 1]
            start = item_left.timing
            end = item_right.timing
            width = end - start
            c = TIMELINE_COLORS[item_left.level]
            string = f'<rect x="{start}" y="0" width="{width}" height="{SVG_HEIGHT}" style="fill:{c}" />\n'
            svg_string += string

        svg_string += "</svg>\n"

        return svg_string

    def get_effect_timelines_meta(self) -> dict[str, str]:
        """outputs {0: '1', 1: '2', 2: '4', 3: '8', 4: '16', 5: '32', 6: 'inf'}"""
        # todo: get rid of this
        steps = [2**x for x in range(6)]
        steps.append("inf")
        return {str(index): step for index, step in enumerate(steps)}

    def get_color_palette(self) -> list[str]:
        # ─── Add Controls Color Palette ───────────────────────────────
        n_colors = 11
        color_palette = [ColorHandler.get_color_from_hue(hue) for hue in np.linspace(0, 1, n_colors + 1)[:-1]] + [
            Color(1, 1, 1)
        ]
        return [f"rgb({int(r*255)},{int(g*255)},{int(b*255)})" for (r, g, b) in color_palette]

    def get_device_meta(self) -> list[dict[str, Any]]:
        resource_fields_devices = {
            "device_index": fields.Integer,
            "n_leds": fields.Integer,
            "n_lights": fields.Integer,
            "is_prim": fields.Boolean,
        }

        return marshal(self.root.devices, resource_fields_devices)
