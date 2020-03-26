import pytest

from model.base_model import BaseModel


def get_base_model(problem):
    return BaseModel("test", problem)


@pytest.mark.parametrize("problem_name, expected", [
    ("rproblem2", [0]),
    ("rproblem3", [0])

])
def test_model_competencies(problem_name, expected):

    base_model = get_base_model(problem_name)

    assert base_model.competencies == expected


@pytest.mark.parametrize("problem_name, expected_length, expected_start", [
    ("rproblem2", 1170, [8.0, 8.5, 9, 9.5]),
    ("rproblem3", 1176, [7.75, 8.0, 8.25, 8.5])

])
def test_model_time_periods(problem_name, expected_length, expected_start):

    base_model = get_base_model(problem_name)
    time_periods = base_model.time_set["periods"][0]

    assert len(time_periods) == expected_length
    assert time_periods[:4] == expected_start


@pytest.mark.parametrize("problem_name, expected_length, expected_start", [
    ("rproblem2", 10, [8.0, 8.5, 9, 9.5]),
    ("rproblem3", 4, [7.75, 8.0, 8.25, 8.5])

])
def test_model_time_periods_in_week(problem_name, expected_length, expected_start):

    base_model = get_base_model(problem_name)
    time_periods = base_model.time_set["periods"][1]

    assert len(time_periods) == expected_length
    assert time_periods[0][:4] == expected_start
