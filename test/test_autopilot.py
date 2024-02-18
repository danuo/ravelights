from unittest.mock import ANY, patch

import pytest
from ravelights.core.settings import Settings  # noqa: F401


def test_autopilot_color_primary(app_render_patched_3):
    app = app_render_patched_3
    settings_autopilot = app.settings.settings_autopilot

    app.settings.enable_autopilot = True

    # test color_primary
    assert "color_primary" in settings_autopilot
    settings_autopilot["color_primary"] = False
    settings_autopilot["p_color_primary"] = 0.9
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


def test_autopilot_triggers(app_render_patched_3):
    app = app_render_patched_3
    settings_autopilot = app.settings.settings_autopilot

    app.settings.enable_autopilot = True

    # test triggers
    assert "triggers" in settings_autopilot

    with patch("ravelights.core.settings.Settings.renew_trigger") as mock_renew_trigger:
        settings_autopilot["triggers"] = False
        settings_autopilot["p_triggers"] = 0.9
        for _ in range(200):
            app.render_frame()
        mock_renew_trigger.assert_not_called()

        settings_autopilot["triggers"] = True
        settings_autopilot["p_triggers"] = 0.0
        for _ in range(200):
            app.render_frame()
        mock_renew_trigger.assert_not_called()

        settings_autopilot["triggers"] = True
        settings_autopilot["p_triggers"] = 0.9
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
