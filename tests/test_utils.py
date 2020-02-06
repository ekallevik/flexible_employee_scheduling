import pytest

from source import utils


@pytest.fixture()
def time_start():
    return [0, 0]\


@pytest.fixture()
def time_end():
    return [2, 30]


@pytest.fixture()
def time_step():
    return 30


def test_time_generator(time_start, time_step, time_end):
    """ Test that the generator yields the expected values"""

    time_iter = utils.time_generator(time_start, time_step, time_end)

    assert next(time_iter) == [0, 0]
    assert next(time_iter) == [0, 30]
    assert next(time_iter) == [1, 0]
    assert next(time_iter) == [1, 30]
    assert next(time_iter) == [2, 0]


def test_time_generator_raises_error_when_end_is_reached(time_start, time_step):
    """ Test that the generator raises StopIteration when the end is reached """

    time_end = [0, 30]
    time_iter = utils.time_generator(time_start, time_step, time_end)

    with pytest.raises(StopIteration):
        next(time_iter)
        next(time_iter)


def test_time_generator_in_for_loop(time_start, time_step, time_end):
    """ Test the generator in a for loop"""

    for time in utils.time_generator(time_start, time_step, time_end):
        assert time[0] < time_end[0] or time[0] == time_end[0] or time[1] < time_end[1]
