import pytest

from gurobipy import *

import xml_loader.xml_loader as xml_loader
from xml_loader import shift_generation


def get_root(problem_name):
    return xml_loader.get_root(problem_name)


@pytest.fixture
def time_periods():
    root = get_root("problem12")
    days = shift_generation.get_days(root)
    time_periods, time_periods_in_week = shift_generation.get_time_periods(root)
    return time_periods, time_periods_in_week, days


@pytest.fixture
def durations():
    # Possible to run on any dataset. Depends on get_events being correct
    root = get_root("problem12")
    return shift_generation.get_durations(root), shift_generation.get_events(root)


@pytest.fixture
def events():
    root = get_root("problem12")
    return shift_generation.get_events(root)


@pytest.fixture
def shifts():
    # Possible to run on any dataset. Dependent on get_durations being correct
    root = get_root("problem12")
    return shift_generation.get_shift_lists(root), shift_generation.get_durations(root)


def test_time_periods(time_periods):
    assert time_periods[0][0] == 0
    assert time_periods[0][-1] == len(time_periods[2]) * 24 - 1


def test_events(events):
    assert events == (
        [
            0.0,
            12.0,
            24.0,
            36.0,
            48.0,
            60.0,
            72.0,
            84.0,
            96.0,
            102.0,
            108.0,
            114.0,
            120.0,
            126.0,
            132.0,
            138.0,
            144.0,
            150.0,
            156.0,
            162.0,
            168.0,
        ]
    ), "The created events are incorrect"


def test_durations(durations):
    for t in durations[0]:
        ind = durations[1].index(t)
        for length in range(len(durations[0][t])):
            assert durations[0][t][length] == (durations[1][ind + (length + 1)] - durations[1][ind])


def test_shifts(shifts):
    for shift in shifts[0][0]:
        assert shift[0] in shifts[1]
        assert shift[1] in shifts[1][shift[0]]


@pytest.mark.parametrize("problem_name, expected", [("problem12", 1),])
def test_time_step(problem_name, expected):

    root = get_root(problem_name)
    time_step = shift_generation.get_time_steps(root)

    assert time_step == expected


@pytest.mark.parametrize("problem_name, expected", [("rproblem2", [0]), ("rproblem3", [0])])
def test_get_competencies(problem_name, expected):

    root = get_root(problem_name)
    competencies = shift_generation.get_competencies(root)

    assert competencies == expected


@pytest.mark.parametrize(
    "problem_name, expected_length, expected_start",
    [("rproblem2", 1170, [8.0, 8.5, 9, 9.5]), ("rproblem3", 1176, [7.75, 8.0, 8.25, 8.5]),],
)
def test_get_time_periods(problem_name, expected_length, expected_start):

    root = get_root(problem_name)
    time_periods = shift_generation.get_time_periods(root)[0]

    assert len(time_periods) == expected_length
    assert time_periods[:4] == expected_start


@pytest.mark.parametrize(
    "problem_name, day, expected",
    [
        ("rproblem2", 0, [(8.0, 8.5), (8.5, 15.5), (15.5, 16.0)]),
        (
            "rproblem3",
            0,
            [
                (7.75, 9.0),
                (9.0, 14.0),
                (14.0, 14.5),
                (14.5, 15.0),
                (15.0, 15.5),
                (15.5, 16.0),
                (16.0, 16.5),
                (16.5, 17.0),
                (17.0, 18.25),
            ],
        ),
    ],
)
def test_get_demand_pairs(problem_name, day, expected):

    root = get_root(problem_name)
    daily_demand = shift_generation.get_days_with_demand(root)

    demand_pairs = shift_generation.get_demand_pairs(daily_demand[day], day)

    assert demand_pairs == expected


@pytest.mark.parametrize(
    "problem_name, day, expected",
    [
        ("rproblem2", 0, [[8.0, 8.5, 15.5, 16.0]]),
        ("rproblem3", 0, [[7.75, 9.0, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 18.25]]),
        ("rproblem4", 0, [[0.0, 6.75], [21.75, 24.0]]),
    ],
)
def test_get_day_demand_intervals(problem_name, day, expected):

    root = get_root(problem_name)
    daily_demand = shift_generation.get_days_with_demand(root)

    day_demand_intervals = shift_generation.get_day_demand_intervals(daily_demand[day], day)

    assert day_demand_intervals == expected


@pytest.mark.parametrize(
    "problem_name, day, expected",
    [
        ("rproblem2", 0, [[8.0, 8.5, 15.5, 16.0]]),
        ("rproblem3", 0, [[7.75, 9.0, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 18.25]]),
    ],
)
def test_get_demand_intervals(problem_name, day, expected):

    root = get_root(problem_name)
    day_demand_intervals = shift_generation.get_demand_intervals(root)

    assert day_demand_intervals[day] == expected


@pytest.mark.parametrize(
    "problem_name, index, expected",
    [
        ("rproblem2", 0, [8.0, 8.5, 15.5, 16.0]),
        ("rproblem3", 0, [7.75, 9.0, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 18.25]),
        ("rproblem4", 1, [21.75, 24.0, 30.75]),
    ],
)
def test_combine_demand_intervals(problem_name, index, expected):

    root = get_root(problem_name)
    combined_demand_intervals = shift_generation.combine_demand_intervals(root)

    assert combined_demand_intervals[index] == expected


@pytest.mark.parametrize(
    "problem_name, day, expected",
    [
        ("rproblem2", 0, [(8.0, 7.5), (8.0, 8.0), (8.5, 7.0), (8.5, 7.5)]),
        (
            "rproblem3",
            0,
            [
                (7.75, 6.25),
                (7.75, 6.75),
                (7.75, 7.25),
                (7.75, 7.75),
                (7.75, 8.25),
                (7.75, 8.75),
                (7.75, 9.25),
                (7.75, 10.5),
                (9.0, 6.0),
                (9.0, 6.5),
                (9.0, 7.0),
                (9.0, 7.5),
                (9.0, 8.0),
                (9.0, 9.25),
            ],
        ),
    ],
)
def test_get_shift_lists(problem_name, day, expected):

    root = get_root(problem_name)
    shift_lists, shift_lists_per_day = shift_generation.get_shift_lists(root)

    assert shift_lists[day] == shift_lists_per_day[day][0]
    assert shift_lists_per_day[day] == expected


@pytest.mark.parametrize(
    "problem_name, day, expected",
    [
        (
            "problem12",
            0,
            [
                (96.0, 6.0),
                (96.0, 12.0),
                (102.0, 6.0),
                (102.0, 12.0),
                (108.0, 6.0),
                (120.0, 6.0),
                (120.0, 12.0),
                (126.0, 6.0),
                (126.0, 12.0),
                (132.0, 6.0),
                (144.0, 6.0),
                (144.0, 12.0),
                (150.0, 6.0),
                (150.0, 12.0),
                (156.0, 6.0),
            ],
        ),
    ],
)
def test_get_shift_lists_does_not_contain_duplicates(problem_name, day, expected):

    root = get_root(problem_name)
    shift_lists, shift_lists_per_day = shift_generation.get_shift_lists(root)

    assert len(set(shift_lists)) == len(shift_lists)
    assert len(set(shift_lists_per_day)) == len(shift_lists_per_day)
    assert shift_lists == expected


@pytest.mark.parametrize(
    "data, expected",
    [([(6, 6), (6, 6), (6, 12)], [(6, 6), (6, 12)]), ([(6, 6), (6, 12)], [(6, 6), (6, 12)]),],
)
def test_remove_duplicate_elements_from_tuplelist(data, expected):

    shifts = tuplelist(data)

    shifts = shift_generation.remove_duplicate_elements_from_tuplelist(shifts)

    assert shifts == expected
    assert type(shifts) == tuplelist
