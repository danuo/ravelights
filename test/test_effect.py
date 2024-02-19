from ravelights.core.effect_super import FramesPattern, get_frames_pattern_binary


def test_get_frames_pattern_binary() -> None:
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


def test_effect_frames_limit(app_time_patched_1) -> None:
    app = app_time_patched_1
    app.settings.enable_autopilot = False

    # get 3 effect names
    effect_name = app.meta_handler.api_content["available_generators"]["effect"][0]["generator_name"]

    # add effects with 15 frames duration
    app.effect_handler.clear_qeueues()
    assert len(app.effect_handler.effect_queue) == 0
    app.effect_handler.load_effect_frames(effect_name=effect_name, limit_frames=15)
    assert len(app.effect_handler.effect_queue) == 1

    active_log: list[bool] = []
    for _ in range(30):
        app.render_frame()
        if app.effect_handler.effect_queue:
            active_log.append(app.effect_handler.effect_queue[0].active)

    # count should be 15
    assert active_log == [True] * 15
    assert sum(active_log) == 15


def test_effect_frames_limit_pattern(app_time_patched_1) -> None:
    app = app_time_patched_1
    app.settings.enable_autopilot = False

    # get 3 effect names
    effect_name = app.meta_handler.api_content["available_generators"]["effect"][0]["generator_name"]

    # add effects with 15 frames duration
    app.effect_handler.clear_qeueues()
    assert len(app.effect_handler.effect_queue) == 0
    frames_pattern = FramesPattern(4, (1,))
    app.effect_handler.load_effect_frames(effect_name=effect_name, limit_frames=8, frames_pattern=frames_pattern)
    assert len(app.effect_handler.effect_queue) == 1

    active_log: list[bool] = []
    for _ in range(30):
        app.render_frame()
        if app.effect_handler.effect_queue:
            active_log.append(app.effect_handler.effect_queue[0].active)

    assert active_log[:8] == [False, True, False, False] * 2
    assert sum(active_log) == 2


def test_effect_frames_limit_pattern_alternating_multi(app_time_patched_1) -> None:
    app = app_time_patched_1
    app.settings.enable_autopilot = False

    # get 3 effect names
    effect_name = app.meta_handler.api_content["available_generators"]["effect"][0]["generator_name"]

    # add effects with 15 frames duration
    app.effect_handler.clear_qeueues()
    frames_pattern = FramesPattern(4, (1,))
    app.effect_handler.load_effect_frames(
        effect_name=effect_name,
        limit_frames=8,
        frames_pattern=frames_pattern,
        multi=2,
    )

    active_log: list[bool] = []
    for _ in range(30):
        app.render_frame()
        if app.effect_handler.effect_queue:
            active_log.append(app.effect_handler.effect_queue[0].active)

    assert active_log[:8] == [False, False, True, True, False, False, False, False]
    assert sum(active_log) == 2
