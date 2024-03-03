from unittest.mock import ANY, patch

import pytest
from ravelights import RaveLightsApp
from ravelights.configs.components import blueprint_timelines
from ravelights.core.settings import Settings  # noqa: F401


def disable_all_autopilot(app: RaveLightsApp) -> None:
    # todo
    settings = app.settings
    PREFIX = "auto_"
    for key in settings.__dict__:
        if isinstance(getattr(settings, key), bool):
            setattr(settings, key, False)


def test_autopilot_color_primary(app_render_patched_3: RaveLightsApp):
    app = app_render_patched_3
    settings = app.settings

    app.settings.enable_autopilot = True

    # test color_primary
    assert hasattr(settings, "auto_color_primary")
    settings.auto_color_primary = False
    settings.auto_p_color_primary = 0.9
    color_primary_before, color_secondary_before = app.settings.color_engine.get_colors_rgb(1)
    for _ in range(2_000):
        app.render_frame()
    color_primary_after, color_secondary_after = app.settings.color_engine.get_colors_rgb(1)
    assert color_primary_before == color_primary_after

    settings.auto_color_primary = True
    settings.auto_p_color_primary = 0.0
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
    settings.auto_p_color_primary = 0.5
    for _ in range(1_000):
        app.render_frame()
        color_primary_now, color_secondary_now = app.settings.color_engine.get_colors_rgb(1)
        if color_primary_before != color_primary_now:
            value_has_changed = True
            break
    assert value_has_changed is True


def test_autopilot_triggers(app_render_patched_3: RaveLightsApp):
    app = app_render_patched_3
    disable_all_autopilot(app)
    settings = app.settings
    app.settings.enable_autopilot = True

    # test triggers
    assert hasattr(settings, "auto_triggers")

    with patch("ravelights.core.settings.Settings.renew_trigger") as mock_renew_trigger:
        settings.auto_triggers = False
        settings.auto_p_triggers = 0.9
        for _ in range(200):
            app.render_frame()
        mock_renew_trigger.assert_not_called()

        settings.auto_triggers = True
        settings.auto_p_triggers = 0.0
        for _ in range(200):
            app.render_frame()
        mock_renew_trigger.assert_not_called()

        settings.auto_triggers = True
        settings.auto_p_triggers = 0.9
        for _ in range(1000):
            app.render_frame()

        mock_renew_trigger.assert_called()

        mock_renew_trigger.assert_any_call(device_index=0, gen_type=ANY, timeline_level=ANY)
        mock_renew_trigger.assert_any_call(device_index=1, gen_type=ANY, timeline_level=ANY)
        mock_renew_trigger.assert_any_call(device_index=2, gen_type=ANY, timeline_level=ANY)

        mock_renew_trigger.assert_any_call(device_index=ANY, gen_type="pattern", timeline_level=ANY)
        mock_renew_trigger.assert_any_call(device_index=ANY, gen_type="pattern_sec", timeline_level=ANY)
        mock_renew_trigger.assert_any_call(device_index=ANY, gen_type="pattern_break", timeline_level=ANY)
        mock_renew_trigger.assert_any_call(device_index=ANY, gen_type="vfilter", timeline_level=ANY)
        mock_renew_trigger.assert_any_call(device_index=ANY, gen_type="dimmer", timeline_level=ANY)
        mock_renew_trigger.assert_any_call(device_index=ANY, gen_type="thinner", timeline_level=ANY)

        mock_renew_trigger.assert_any_call(device_index=ANY, gen_type=ANY, timeline_level=1)
        mock_renew_trigger.assert_any_call(device_index=ANY, gen_type=ANY, timeline_level=2)
        mock_renew_trigger.assert_any_call(device_index=ANY, gen_type=ANY, timeline_level=3)

        with pytest.raises(Exception):
            mock_renew_trigger.assert_any_call(device_index=ANY, gen_type=ANY, timeline_level=0)

        with pytest.raises(Exception):
            mock_renew_trigger.assert_any_call(device_index=ANY, gen_type=ANY, timeline_level=4)


def test_autopilot_timeline_placement(app_render_patched_3: RaveLightsApp):
    app = app_render_patched_3
    settings = app.settings

    settings.enable_autopilot = True

    # test triggers
    assert hasattr(settings, "auto_triggers")

    with patch("ravelights.core.pattern_scheduler.PatternScheduler.load_timeline_by_index") as mock_load_timeline:
        settings.auto_timeline_placement = False
        settings.auto_p_timeline_placement = 0.9
        for _ in range(200):
            app.render_frame()
        mock_load_timeline.assert_not_called()

        settings.auto_timeline_placement = True
        settings.auto_p_timeline_placement = 0.0
        for _ in range(200):
            app.render_frame()
        mock_load_timeline.assert_not_called()

        settings.auto_timeline_placement = True
        settings.auto_p_timeline_placement = 0.9
        for _ in range(1000):
            app.render_frame()

        mock_load_timeline.assert_called()

        for item in mock_load_timeline.mock_calls:
            timeline_index = item.args[0]
            assert blueprint_timelines[timeline_index]["meta"].weight != 0
