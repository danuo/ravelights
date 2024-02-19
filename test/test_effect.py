from unittest.mock import patch

from ravelights.core.effect_super import FramesPattern, get_frames_pattern_binary


def test_get_frames_pattern_binary():
    frames_pattern = FramesPattern(4, (0,))

    result = get_frames_pattern_binary(frames_pattern)
    assert result == [True, False, False, False]

    result = get_frames_pattern_binary(frames_pattern, multi=1)
    assert result == [True, False, False, False]

    result = get_frames_pattern_binary(frames_pattern, multi=2)
    assert result == [True, True, False, False, False, False, False, False]

    frames_pattern = FramesPattern(3, (0, 2))
    result = get_frames_pattern_binary(frames_pattern, multi=2)
    assert result == [True, True, False, False, True, True]


def test_effect_frames_limit(app_time_patched_2):
    app = app_time_patched_2
    app.settings.enable_autopilot = False

    # get 3 effect names
    effect_names = [e["generator_name"] for e in app.meta_handler.api_content["available_generators"]["effect"][:3]]

    # add effects with 15 frames duration
    for effect_name in effect_names:
        app.effect_handler.clear_qeueues()
        assert len(app.effect_handler.effect_queue) == 0
        app.effect_handler.load_effect_frames(effect_name=effect_name, limit_frames=15)
        assert len(app.effect_handler.effect_queue) == 1

        for _ in range(10):
            app.render_frame()

        assert len(app.effect_handler.effect_queue) == 1

        for _ in range(10):
            app.render_frame()

        assert len(app.effect_handler.effect_queue) == 0


"""
def test_effect_frames_limit_pattern(app_time_patched_2):
    app = app_time_patched_2
    app.settings.enable_autopilot = False

    # get 3 effect names
    effect_name = app.meta_handler.api_content["available_generators"]["effect"][0]["generator_name"]

    # add effects with 15 frames duration
    with patch("ravelights.core.render_module.RenderModule.render") as mocked_function
        app.effect_handler.clear_qeueues()
        assert len(app.effect_handler.effect_queue) == 0
        app.effect_handler.load_effect_frames(effect_name=effect_name, limit_frames=15)
        assert len(app.effect_handler.effect_queue) == 1

        for _ in range(10):
            app.render_frame()

        assert len(app.effect_handler.effect_queue) == 1

        for _ in range(10):
            app.render_frame()

        assert len(app.effect_handler.effect_queue) == 0

"""
