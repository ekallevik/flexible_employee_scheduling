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




@pytest.mark.parametrize("day, time_step, expected", [
    [0, 15, [i for i in range(24*4)]],
    [0, 30, [i for i in range(24*2)]],
    [0, 60, [i for i in range(24)]],
    [1, 60, [i for i in range(24, 24*2)]],
    [2, 60, [i for i in range(24*2, 24*3)]]
])
def test_times_in_day(day, time_step, expected):

    times_in_day = utils.times_in_day(day, time_step)
    times = []

    for time in times_in_day:
        times.append(time)

    assert times == expected


@pytest.mark.parametrize("time_step, expected", [
    [60, 24],
    [30, 48],
    [15, 96]
])
def test_get_day_size(time_step, expected):

    assert utils.get_day_size(time_step) == expected