from ravelights.effects.effect_super import FramesPattern, get_frames_pattern_binary


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
