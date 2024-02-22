from ravelights.core.autopilot import CONTROLS_AUTOPILOT
from ravelights.core.meta_handler import CONTROLS_GLOBAL_SLIDERS


def test_autopilot_controls(app_1):
    # checks that all controls in AUTOPILOT_CONTROLS have a valid setting in settings_autopilot
    settings_autopilot = app_1.settings.settings_autopilot

    for item in CONTROLS_AUTOPILOT:
        if item.type == "toggle_slider":
            assert item.name_toggle in settings_autopilot
            assert isinstance(settings_autopilot[item.name_toggle], bool)
            assert item.name_slider in settings_autopilot
            assert isinstance(settings_autopilot[item.name_slider], float) or isinstance(
                settings_autopilot[item.name_slider], int
            )
        if item.type == "slider":
            assert item.name_slider in settings_autopilot
            assert isinstance(settings_autopilot[item.name_slider], float) or isinstance(
                settings_autopilot[item.name_slider], int
            )


def test_controls_global_sliders(app_1):
    # checks that all setting vars in CONTROLS_GLOBAL_SLIDERS are present in settings
    settings = app_1.settings

    for item in CONTROLS_GLOBAL_SLIDERS:
        if item.type == "slider":
            assert hasattr(settings, item.name_slider)
            assert isinstance(getattr(settings, item.name_slider), float) or isinstance(
                getattr(settings, item.name_slider), int
            )
