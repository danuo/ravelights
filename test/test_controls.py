from ravelights.core.controls import CONTROLS_AUDIO, CONTROLS_AUTOPILOT, CONTROLS_GLOBAL_SLIDERS
from ravelights.core.custom_typing import Dropdown, PaddedSlider, Slider, Toggle, ToggleSlider


def test_controls_autopilot(app_1):
    # checks that all controls in AUTOPILOT_CONTROLS have a valid setting in settings
    settings = app_1.settings
    check_if_controls_in_settings(CONTROLS_AUTOPILOT, settings)


def test_controls_global_sliders(app_1):
    # checks that all controls in AUTOPILOT_CONTROLS have a valid setting in settings
    settings = app_1.settings
    check_if_controls_in_settings(CONTROLS_GLOBAL_SLIDERS, settings)


def test_controls_audio(app_1):
    # checks that all controls in AUTOPILOT_CONTROLS have a valid setting in settings
    settings = app_1.settings
    check_if_controls_in_settings(CONTROLS_AUDIO, settings)


def check_if_controls_in_settings(controls: list[Dropdown | Toggle | Slider | PaddedSlider | ToggleSlider], settings):
    for item in CONTROLS_AUTOPILOT:
        if isinstance(item, Dropdown):
            assert hasattr(settings, item.var_name)
            assert isinstance(getattr(settings, item.var_name), str)
        elif isinstance(item, Slider):  # also includes PaddedSlider
            assert hasattr(settings, item.var_name)
            assert isinstance(getattr(settings, item.var_name), float) or isinstance(
                getattr(settings, item.var_name), int
            )
        elif isinstance(item, Toggle):
            assert hasattr(settings, item.var_name)
            assert isinstance(getattr(settings, item.var_name), bool)
        elif isinstance(item, ToggleSlider):
            assert hasattr(settings, item.var_name_toggle)
            assert getattr(settings, item.var_name_toggle)
            assert isinstance(getattr(settings, item.var_name_toggle), bool)
            assert hasattr(settings, item.var_name_slider)
            assert isinstance(getattr(settings, item.var_name_slider), float) or isinstance(
                getattr(settings, item.var_name_slider), int
            )
