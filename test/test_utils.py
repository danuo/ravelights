import pytest
from ravelights.core.utils import LightSequenceGenerator, map_value


@pytest.mark.parametrize(
    "expected, test_input",
    [
        (0.0, (4, (0, 2), (4, 5))),
        (1.0, (4.5, (0, 2), (4, 5))),
        (2.0, (5.0, (0, 2), (4, 5))),
        (0.0, (0, (0, 2))),
        (1.0, (0.5, (0, 2))),
        (2.0, (1.0, (0, 2))),
    ],
)
def test_eval(expected: float, test_input):
    assert expected == map_value(*test_input)


def test_light_sequence_output_length():
    N_LIGHTS = 1
    light_indices_list = LightSequenceGenerator.left_to_right(N_LIGHTS)
    assert len(light_indices_list) == 1
    light_indices_list = LightSequenceGenerator.left_to_right(N_LIGHTS, reverse=True)
    assert len(light_indices_list) == 1
    light_indices_list = LightSequenceGenerator.out_to_mid(N_LIGHTS)
    assert len(light_indices_list) == 1
    light_indices_list = LightSequenceGenerator.out_to_mid(N_LIGHTS, reverse=True)
    assert len(light_indices_list) == 1


def test_light_sequence_left_to_right_even():
    N_ITEMS = 6
    left_to_right = LightSequenceGenerator.left_to_right(N_ITEMS)
    assert len(left_to_right) == N_ITEMS
    assert left_to_right == [(0,), (1,), (2,), (3,), (4,), (5,)]

    right_to_left = LightSequenceGenerator.left_to_right(N_ITEMS, reverse=True)
    assert len(right_to_left) == N_ITEMS
    assert right_to_left == [(5,), (4,), (3,), (2,), (1,), (0,)]


def test_light_sequence_out_to_mid_even():
    N_ITEMS = 6
    out_to_mid = LightSequenceGenerator.out_to_mid(N_ITEMS)
    assert len(out_to_mid) == 3
    assert out_to_mid == [(0, 5), (1, 4), (2, 3)]

    mid_to_out = LightSequenceGenerator.out_to_mid(N_ITEMS, reverse=True)
    assert len(mid_to_out) == 3
    assert mid_to_out == [(2, 3), (1, 4), (0, 5)]


def test_light_sequence_left_to_right_uneven():
    N_ITEMS = 5
    left_to_right = LightSequenceGenerator.left_to_right(N_ITEMS)
    assert len(left_to_right) == 5
    assert left_to_right == [(0,), (1,), (2,), (3,), (4,)]

    right_to_left = LightSequenceGenerator.left_to_right(N_ITEMS, reverse=True)
    assert len(right_to_left) == 5
    assert right_to_left == [(4,), (3,), (2,), (1,), (0,)]


def test_light_sequence_out_to_mid_uneven():
    N_ITEMS = 5
    out_to_mid = LightSequenceGenerator.out_to_mid(N_ITEMS)
    assert len(out_to_mid) == 3
    assert out_to_mid == [(0, 4), (1, 3), (2,)]

    mid_to_out = LightSequenceGenerator.out_to_mid(N_ITEMS, reverse=True)
    assert len(mid_to_out) == 3
    assert mid_to_out == [(2, 3), (1, 4), (0,)]
