import pytest
from ravelights.core.utils import map_value


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
