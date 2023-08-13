from collections import namedtuple
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Iterable, Type, cast

from ravelights.configs.components import Keywords, blueprint_effects, blueprint_generators, blueprint_timelines
from ravelights.core.colorhandler import COLOR_TRANSITION_SPEEDS
from ravelights.core.generator_super import Generator
from ravelights.core.templateobjects import GenPlacing
from ravelights.effects.effect_super import Effect

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp

Item = namedtuple("Item", field_names="timing level")

SVG_HEIGHT = 70
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
        self.api_content = dict()
        self.api_content["available_timelines"] = self.get_meta_available_timelines()
        self.api_content["available_keywords"] = self.get_meta_available_keywords()
        self.api_content["available_generators"] = self.get_meta_available_generators()
        self.api_content["controls_global_sliders"] = self.get_controls_global_sliders()
        self.api_content["controls_live_generator"] = self.set_controls_generators_live()
        self.api_content["available_timelines_svg"] = self.get_all_timeline_svgs()  # formerly meta / timelines
        self.api_content["steps_dict"] = self.get_effect_timelines_meta()
        self.api_content["color_transition_speeds"] = [x.value for x in COLOR_TRANSITION_SPEEDS]
        self.api_content["controls_autopilot"] = self.root.autopilot.get_autopilot_controls()
        self.api_content["controls_color_palette"] = self.root.autopilot.get_color_palette()

    def __getitem__(self, key):
        return self.api_content[key]

    def __setitem__(self, key, value):
        self.api_content[key] = value

    def get_meta_available_timelines(self) -> list[str]:
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
        # todo: move this to meta, do not get this from blueprint directly
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

    def get_controls_global_sliders(self):
        controls_global_sliders = [
            dict(type="slider", var_name="bpm_base", range_min=40, range_max=200, step=1, markers=False),
            dict(type="slider", var_name="global_brightness", range_min=0.0, range_max=1.0, step=0.1, markers=True),
            dict(type="slider", var_name="global_energy", range_min=0.0, range_max=1.0, step=0.1, markers=True),
            dict(type="slider", var_name="global_thinning_ratio", range_min=0.0, range_max=1.0, step=0.1, markers=True),
            dict(type="slider", var_name="global_skip_trigger", range_min=1, range_max=8, step=1, markers=True),
        ]
        return controls_global_sliders

    def set_controls_generators_live(self):
        """Generates buttons for alternate, reset and on_trigger command for the generator types
        pattern, vfilter, thinner and dimmer."""
        out = []
        for ident in self.root.settings.generator_classes_identifiers[:4]:
            for command in ["alternate", "new trigger", "on_trigger"]:
                out.append(dict(name=f"{ident} {command}", gen_type=ident, action="gen_command", command=command))
        return out

    def get_all_timeline_svgs(self):
        names = []
        descriptions = []
        svgs = []
        colors = [c for c in TIMELINE_COLORS.values()]
        for timeline in blueprint_timelines:
            names.append(timeline["meta"].get("name", "unnamed"))
            descriptions.append(timeline["meta"].get("description", "no description"))
            svgs.append(self.get_svg_for_timeline(timeline))
        self.root.settings.meta["timelines"] = dict(names=names, descriptions=descriptions, svgs=svgs, colors=colors)

    def get_svg_for_timeline(self, timeline):
        placements = timeline["placements"]
        items = []
        for placement in placements:
            if placement.cls != GenPlacing:
                continue

            level = placement.args["level"]
            timings = placement.args["timings"]
            for t in timings:
                item = Item(t, level)
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
