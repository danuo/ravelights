import pytest
from ravelights import RaveLightsApp
from ravelights.core.autopilot import AUTOPILOT_CONTROLS


@pytest.fixture
def app_autopilot_disabled(app_time_patched) -> RaveLightsApp:
    settings_autopilot = app_time_patched.settings.settings_autopilot
    for key, value in settings_autopilot.items():
        if isinstance(value, bool):
            settings_autopilot[key] = False

    # turn on autopilot
    app_time_patched.settings.enable_autopilot = False
    return app_time_patched


def test_autopilot_color_primary(app_autopilot_disabled):
    app = app_autopilot_disabled
    settings_autopilot = app_autopilot_disabled.settings.settings_autopilot

    app.settings.enable_autopilot = True

    # test color_primary
    assert "color_primary" in settings_autopilot
    color_primary_before, color_secondary_before = app.settings.color_engine.get_colors_rgb(1)
    for _ in range(2_000):
        app.render_frame()
    color_primary_after, color_secondary_after = app.settings.color_engine.get_colors_rgb(1)
    assert color_primary_before == color_primary_after

    settings_autopilot["color_primary"] = True
    settings_autopilot["p_color_primary"] = 0.0
    value_has_changed = False
    color_primary_before, color_secondary_before = app.settings.color_engine.get_colors_rgb(1)

    # check with p = 0 -> nothing should happen
    for _ in range(1_000):
        app.render_frame()
        color_primary_now, color_secondary_now = app.settings.color_engine.get_colors_rgb(1)
        if color_primary_before != color_primary_now:
            value_has_changed = True
            break
    assert value_has_changed is False

    # check with p = 0.5 -> color should change
    settings_autopilot["p_color_primary"] = 0.5
    for _ in range(1_000):
        app.render_frame()
        color_primary_now, color_secondary_now = app.settings.color_engine.get_colors_rgb(1)
        if color_primary_before != color_primary_now:
            value_has_changed = True
            break
    assert value_has_changed is True


def test_autopilot_controls(app_normal):
    # checks that all controls in AUTOPILOT_CONTROLS have a valid setting in settings_autopilot
    settings_autopilot = app_normal.settings.settings_autopilot

    for item in AUTOPILOT_CONTROLS:
        if item["type"] == "toggle_slider":
            assert item["name_toggle"] in settings_autopilot
            assert isinstance(settings_autopilot[item["name_toggle"]], bool)
            assert item["name_slider"] in settings_autopilot
            assert isinstance(settings_autopilot[item["name_slider"]], float) or isinstance(
                settings_autopilot[item["name_slider"]], int
            )
        if item["type"] == "slider":
            assert item["name_slider"] in settings_autopilot
            assert isinstance(settings_autopilot[item["name_slider"]], float) or isinstance(
                settings_autopilot[item["name_slider"]], int
            )
