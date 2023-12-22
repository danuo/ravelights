import pytest
from ravelights.core.utils import LightSequence, map_value


@pytest.mark.skip
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


def test_light_sequence_left_to_right():
    seq = LightSequence()

    # test length
    n_items = 5
    left_to_right = seq.left_to_right(n_items)
    assert len(left_to_right) == 1
    assert len(left_to_right[0]) == n_items

    n_items = 5
    right_to_left = seq.left_to_right(n_items, reverse=True)
    assert len(right_to_left[0]) == n_items

    # test content

    assert left_to_right[0] == [0, 1, 2, 3, 4]
    assert right_to_left[0] == [4, 3, 2, 1, 0]


def test_light_sequence_out_to_mid():
    # test length
    n_items = 5
    out_to_mid = LightSequence.out_to_mid(n_items)
    assert len(out_to_mid) == 2
    assert len(out_to_mid[0]) == n_items // 2 + 1
    assert len(out_to_mid[1]) == n_items // 2

    assert out_to_mid[0] == [0, 1, 2]
    assert out_to_mid[1] == [3, 4]

    mid_to_out = LightSequence.out_to_mid(n_items, reverse=True)
    assert len(mid_to_out) == 2
    assert len(mid_to_out[0]) == n_items // 2 + 1
    assert len(mid_to_out[1]) == n_items // 2

    assert mid_to_out[0] == [2, 1, 0]
    assert mid_to_out[1] == [4, 3]
