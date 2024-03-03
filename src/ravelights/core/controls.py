from ravelights.core.custom_typing import Dropdown, PaddedSlider, Slider, Toggle, ToggleSlider
from ravelights.core.settings import AutomateChorus

CONTROLS_AUDIO = [
    Dropdown(var_name="automate_chorus", options=[e.value for e in AutomateChorus]),
    Slider(var_name="global_manual_chorus", range_min=0.0, range_max=1.0, step=0.1, markers=True),
]

CONTROLS_GLOBAL_SLIDERS: list[Slider] = [
    Slider(var_name="global_brightness", range_min=0.0, range_max=1.0, step=0.1, markers=True),
    Slider(var_name="global_energy", range_min=0.0, range_max=1.0, step=0.1, markers=True),
    Slider(var_name="global_thinning_ratio", range_min=0.0, range_max=1.0, step=0.1, markers=True),
    Slider(var_name="global_frameskip", range_min=1, range_max=8, step=1, markers=True),
    Slider(var_name="global_triggerskip", range_min=1, range_max=8, step=1, markers=True),
    Toggle(var_name="visualizer_half_framerate"),
]


CONTROLS_AUTOPILOT: list[Toggle | PaddedSlider | ToggleSlider] = [
    Toggle(
        var_name="enable_autopilot",
    ),
    ToggleSlider(
        var_name_toggle="auto_renew_pattern",
        var_name_slider="auto_p_renew_pattern",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        var_name_toggle="auto_renew_pattern_sec",
        var_name_slider="auto_p_renew_pattern_sec",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        var_name_toggle="auto_renew_vfilter",
        var_name_slider="auto_p_renew_vfilter",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        var_name_toggle="auto_renew_dimmer",
        var_name_slider="auto_p_renew_dimmer",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        var_name_toggle="auto_renew_thinner",
        var_name_slider="auto_p_renew_thinner",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        var_name_toggle="auto_color_primary",
        var_name_slider="auto_p_color_primary",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        var_name_toggle="auto_timeline_placement",
        var_name_slider="auto_p_timeline_placement",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        var_name_toggle="auto_timeline_selector",
        var_name_slider="auto_p_timeline_selector",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    PaddedSlider(
        var_name="auto_p_timeline_selector_individual",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        var_name_toggle="auto_alternate",
        var_name_slider="auto_p_alternate",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    ToggleSlider(
        var_name_toggle="auto_triggers",
        var_name_slider="auto_p_triggers",
        range_min=0.0,
        range_max=1.0,
        step=0.1,
        markers=True,
    ),
    PaddedSlider(
        var_name="auto_loop_length",
        range_min=4,
        range_max=32,
        step=4,
        markers=True,
    ),
]
