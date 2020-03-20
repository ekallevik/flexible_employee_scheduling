import pytest

from model.optimality_model import OptimalityModel


@pytest.fixture()
def optimality_model():
    return OptimalityModel(name="test_model")


@pytest.fixture()
def optimality_constraints(optimality_model):
    return optimality_model.constraints


def test_get_consecutive_days_time_window(optimality_constraints):

    time_window = optimality_constraints.get_consecutive_days_time_window(0)

    assert len(time_window) == optimality_constraints.limit_on_consecutive_days
