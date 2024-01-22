from typing import TYPE_CHECKING, Any, NamedTuple, cast

from ravelights.configs.components import Keywords, blueprint_effects, blueprint_generators, blueprint_timelines
from ravelights.core.blueprints import BlueprintEffect, BlueprintGen
from ravelights.core.color_handler import COLOR_TRANSITION_SPEEDS, SecondaryColorModes
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
    """
    This creates objects/resources that are available via api to create elements of the UI
    """

    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.settings = root.settings
        self.api_content: dict[str, Any] = dict()
        self.api_content["available_timelines"] = self.get_meta_available_timelines()
        self.api_content["available_keywords"] = self.get_meta_available_keywords()
        self.api_content["available_generators"] = self.get_meta_available_generators()
        self.api_content["controls_global_sliders"] = self.get_controls_global_sliders()
        self.api_content["available_timelines_svg"] = self.get_all_timeline_svgs()  # formerly meta / timelines
        self.api_content["steps_dict"] = self.get_effect_timelines_meta()
        self.api_content["color_transition_speeds"] = [x.value for x in COLOR_TRANSITION_SPEEDS]
        self.api_content["controls_autopilot"] = self.root.autopilot.get_autopilot_controls()
        self.api_content["controls_color_palette"] = self.root.autopilot.get_color_palette()
        self.api_content["color_sec_mode_names"] = [mode.value for mode in SecondaryColorModes]

    def __getitem__(self, key: str):
        return self.api_content[key]

    def __setitem__(self, key: str, value: Any):
        self.api_content[key] = value

    def get_meta_available_timelines(self) -> list[str]:
        timeline_names: list[str] = [blue["meta"]["name"] for blue in blueprint_timelines]
        return timeline_names

    def get_meta_available_keywords(self) -> list[str]:
        available_keywords: set[str] = set()
        for item in blueprint_generators + blueprint_effects:
            keywords: list[Keywords] = item.keywords
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

        keys = ["pattern", "vfilter", "thinner", "dimmer", "effect"]
        meta_available_generators: AvailableGenerators = {key: [] for key in keys}
        generators_and_effects = (
            self.root.devices[0].rendermodule.generators_dict | self.root.effecthandler.effect_wrappers_dict
        )
        for generator_name, gen in generators_and_effects.items():
            class_identifier = gen.get_identifier()
            generator_keywords: list[str] = gen.keywords
            generator_weight: float = gen.weight
            meta_available_generators[class_identifier].append(
                {
                    "generator_name": generator_name,
                    "generator_keywords": generator_keywords,
                    "generator_weight": generator_weight,
                }
            )

        return meta_available_generators

    def get_controls_global_sliders(self):
        controls_global_sliders = [
            dict(type="slider", var_name="global_brightness", range_min=0.0, range_max=1.0, step=0.1, markers=True),
            dict(type="slider", var_name="global_energy", range_min=0.0, range_max=1.0, step=0.1, markers=True),
            dict(type="slider", var_name="global_thinning_ratio", range_min=0.0, range_max=1.0, step=0.1, markers=True),
            dict(type="slider", var_name="global_frameskip", range_min=1, range_max=8, step=1, markers=True),
            dict(type="slider", var_name="global_triggerskip", range_min=1, range_max=8, step=1, markers=True),
        ]
        return controls_global_sliders

    def get_all_timeline_svgs(self):
        names = []
        descriptions = []
        svgs = []
        colors = [c for c in TIMELINE_COLORS.values()]
        for timeline in blueprint_timelines:
            names.append(timeline["meta"].get("name", "unnamed"))
            descriptions.append(timeline["meta"].get("description", "no description"))
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

    def get_effect_timelines_meta(self):
        """outputs {0: '1', 1: '2', 2: '4', 3: '8', 4: '16', 5: '32', 6: 'inf'}"""
        # todo: get rid of this
        steps = [2**x for x in range(6)]
        steps.append("inf")
        return {i: s for i, s in enumerate(steps)}
