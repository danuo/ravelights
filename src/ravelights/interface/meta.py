from collections import namedtuple
from typing import TYPE_CHECKING

from ravelights.configs.components import blueprint_timelines
from ravelights.core.colorhandler import COLOR_TRANSITION_SPEEDS
from ravelights.core.templateobjects import GenPlacing

if TYPE_CHECKING:
    from ravelights.core.ravelights_app import RaveLightsApp


Item = namedtuple("Item", field_names="timing level")

HEIGHT = 70
TIMELINE_COLORS = {
    1: "rgb(113,231,255)",
    2: "rgb(55,30,95)",
    3: "rgb(81,255,0)",
}


class MetaControls:
    """
    This creates objects/resources that are available via api to create elements of the UI
    """

    def __init__(self, root: "RaveLightsApp"):
        self.root = root
        self.set_controls_generators_live()
        self.generate_all_svgs()
        self.get_effect_timelines_meta()
        self.set_controls_global_sliders()
        self.root.settings.controls["color_transition_speeds"] = [x.value for x in COLOR_TRANSITION_SPEEDS]

    def set_controls_global_sliders(self):
        controls_global_sliders = [
            dict(type="slider", var_name="bpm_base", range_min=40, range_max=200, step=1, markers=False),
            dict(type="slider", var_name="global_brightness", range_min=0.0, range_max=1.0, step=0.1, markers=True),
            dict(type="slider", var_name="global_energy", range_min=0.0, range_max=1.0, step=0.1, markers=True),
            dict(type="slider", var_name="global_thinning_ratio", range_min=0.0, range_max=1.0, step=0.1, markers=True),
            dict(type="slider", var_name="global_skip_trigger", range_min=1, range_max=8, step=1, markers=True),
        ]
        self.root.settings.controls["controls_global_sliders"] = controls_global_sliders

    def set_controls_generators_live(self):
        """Generates buttons for alternate, reset and on_trigger command for the generator types
        pattern, vfilter, thinner and dimmer."""
        out = []
        for ident in self.root.settings.generator_classes_identifiers[:4]:
            for command in ["alternate", "new trigger", "on_trigger"]:
                out.append(dict(name=f"{ident} {command}", gen_type=ident, action="gen_command", command=command))
        self.root.settings.controls["controls_live_generator"] = out

    def generate_all_svgs(self):
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

        svg_middle = ""
        for i in range(len(items) - 1):
            item_left = items[i]
            item_right = items[i + 1]
            start = item_left.timing
            end = item_right.timing
            width = end - start
            c = TIMELINE_COLORS[item_left.level]
            string = f'<rect x="{start}" y="0" width="{width}" height="{HEIGHT}" style="fill:{c}" />\n'
            svg_middle += string

        svg_start = f'<svg width="100%" height="100%" viewBox="0 0 128 {HEIGHT}" preserveAspectRatio="none">\n'
        svg_end = "</svg>\n"

        return svg_start + svg_middle + svg_end

    def get_effect_timelines_meta(self):
        """outputs {0: '1', 1: '2', 2: '4', 3: '8', 4: '16', 5: '32', 6: 'inf'}"""

        steps = [2**x for x in range(6)]
        steps.append("inf")
        steps_dict = {i: s for i, s in enumerate(steps)}
        self.root.settings.meta["steps_dict"] = steps_dict
