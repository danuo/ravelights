import logging
from dataclasses import dataclass

import numpy as np

from ravelights.core.bpmhandler import BeatStatePattern
from ravelights.core.colorhandler import ColorHandler
from ravelights.core.device import Device
from ravelights.core.settings import Settings
from ravelights.core.utils import p

logger = logging.getLogger(__name__)


@dataclass
class AutoPilot:
    settings: Settings
    devices: list[Device]

    def __post_init__(self):
        self.settings.settings_autopilot = dict(
            autopilot=False,
            loop_length=8,

            autoload_vfilter=True,
            autoload_dimmer=True,
            autoload_thinner=True,
            autoload_triggers=True,

            color_primary=True,
            p_color_primary=0.1,

            color_secondary=True,
            p_color_secondary=0.1,

            color_effect=True,
            p_color_effect=0.1,

            timeline=True,
            p_timeline=0.1,

            pattern=True,
            p_pattern=0.1,

            pattern_sec=True,
            p_pattern_sec=0.1,

            alternate_pattern=True,
            p_alternate_pattern=0.1,

            alternate_pattern_sec=True,
            p_alternate_pattern_sec=0.1,

            triggers=True,
            p_triggers=0.1,
        )

        # ─── Add Controls Autopilot ───────────────────────────────────
        controls_autopilot = [
            dict(type="toggle", name_toggle="autopilot"),
            dict(type="toggle", name_toggle="autoload_vfilter"),
            dict(type="toggle", name_toggle="autoload_dimmer"),
            dict(type="toggle", name_toggle="autoload_thinner"),
            dict(type="toggle", name_toggle="autoload_triggers"),
            dict(type="toggle_slider", name_toggle="color_primary", name_slider="p_color_primary", range_min=0., range_max=1., step=0.1, markers=True),
            dict(type="toggle_slider", name_toggle="color_secondary", name_slider="p_color_secondary", range_min=0., range_max=1., step=0.1, markers=True),
            dict(type="toggle_slider", name_toggle="color_effect", name_slider="p_color_effect", range_min=0., range_max=1., step=0.1, markers=True),
            dict(type="toggle_slider", name_toggle="timeline", name_slider="p_timeline", range_min=0., range_max=1., step=0.1, markers=True),
            dict(type="toggle_slider", name_toggle="pattern", name_slider="p_pattern", range_min=0., range_max=1., step=0.1, markers=True),
            dict(type="toggle_slider", name_toggle="pattern_sec", name_slider="p_pattern_sec", range_min=0., range_max=1., step=0.1, markers=True),
            dict(type="toggle_slider", name_toggle="alternate_pattern", name_slider="p_alternate_pattern", range_min=0., range_max=1., step=0.1, markers=True),
            dict(type="toggle_slider", name_toggle="alternate_pattern_sec", name_slider="p_alternate_pattern_sec", range_min=0., range_max=1., step=0.1, markers=True),
            dict(type="toggle_slider", name_toggle="triggers", name_slider="p_triggers", range_min=0., range_max=1., step=0.1, markers=True),
            dict(type="slider", name_slider="loop_length", range_min=4, range_max=32, step=4, markers=True),
        ]
        self.settings.controls["controls_autopilot"] = controls_autopilot

        # ─── Add Controls Color Palette ───────────────────────────────
        n_colors = 12
        controls_color_palette = [ColorHandler.get_color_from_hue(hue) for hue in np.linspace(0, 1, n_colors+1)[:-1]]
        controls_color_palette = [f"rgb({int(r*255)},{int(g*255)},{int(b*255)})" for (r, g, b) in controls_color_palette]
        self.settings.controls["controls_color_palette"] = controls_color_palette

    def randomize(self) -> None:
        """Called every frame to randomize parameters within ravelights app."""

        if not self.settings.settings_autopilot["autopilot"]:
            return None

        is_triggerd = self.settings.beat_state == BeatStatePattern(loop_length=self.settings.settings_autopilot["loop_length"])
        if not is_triggerd:
            return None

        # ─── Colors ───────────────────────────────────────────────────

        if self.settings.settings_autopilot["color_primary"]:
            if p(self.settings.settings_autopilot["p_color_primary"]):
                self.settings.color[0] = ColorHandler.get_random_color()
        if self.settings.settings_autopilot["color_secondary"]:
            if p(self.settings.settings_autopilot["p_color_secondary"]):
                self.settings.color[1] = ColorHandler.get_random_color()
        if self.settings.settings_autopilot["color_effect"]:
            if p(self.settings.settings_autopilot["p_color_effect"]):
                self.settings.color[2] = ColorHandler.get_random_color()

        # ─── Triggers ─────────────────────────────────────────────────

        if self.settings.settings_autopilot["triggers"]:
            if p(self.settings.settings_autopilot["p_triggers"]):
                for level in range(3):
                    for gen_type in ["WIP"]:
                        pass
