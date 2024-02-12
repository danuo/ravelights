import random

import pytest
from loguru import logger
from ravelights.core.ravelights_app import RaveLightsApp
from ravelights.core.time_handler import BeatStatePattern

# @pytest.fixture(scope="module")
# def ravelights_app():
#     return RaveLightsApp()


def test_autopilot():
    FPS = 20
    global_time = 0

    def get_global_time():
        nonlocal global_time
        return global_time

    def increase_globaltime():
        nonlocal global_time
        norm = random.normalvariate(0, 0.004)
        assert abs(norm) < 1 / FPS
        random_frame_time = 1 / FPS + norm
        global_time += random_frame_time

    app = RaveLightsApp()
    app.time_handler.get_current_time = get_global_time
    app.time_handler.after = increase_globaltime
    app.pattern_scheduler.load_timeline_from_index(1)  # todo: load by name

    # turn all things off
    settings_autopilot = app.settings.settings_autopilot
    for key, value in settings_autopilot.items():
        if isinstance(value, bool):
            settings_autopilot[key] = False

    # turn on autopilot
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
