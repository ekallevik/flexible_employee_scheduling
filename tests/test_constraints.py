import os

import pytest

ENVIRONMENT = os.environ.get("ENVIRONMENT")
print(ENVIRONMENT)
try:
    from gurobipy.gurobipy import Model, GRB
except ModuleNotFoundError:
    pass

from model import constraints, variables

pytestmark = pytest.mark.skipif(
    ENVIRONMENT != "local", reason="This test is dependent on Gurobi, and cannot be run in CircleCI"
)


@pytest.fixture()
def model():
    return Model("employee_scheduling_with_shifts")


@pytest.fixture()
def employees():
    return [0, 1]


@pytest.fixture()
def contracted_hours():
    return [37, 30]


@pytest.fixture()
def competencies():
    return ["comp1", "comp2"]


@pytest.fixture()
def time_periods():
    return [0, 1]


@pytest.fixture()
def days():
    return [0]


@pytest.fixture()
def weeks():
    return [0]


@pytest.fixture()
def days_in_week():
    return [[0]]


@pytest.fixture()
def shifts():
    return [0]


@pytest.fixture()
def off_shifts():
    return [0]


@pytest.fixture()
def min_demand():
    return {"comp1": [1, 0], "comp2": [0, 1]}


@pytest.fixture()
def ideal_demand():
    return {"comp1": [1, 0], "comp2": [0, 1]}


@pytest.fixture()
def max_demand():
    return {"comp1": [2, 0], "comp2": [0, 2]}


@pytest.fixture()
def y(competencies, employees, model, time_periods):
    return variables.add_y(model, competencies, employees, time_periods)


@pytest.fixture()
def x(model, employees, days, shifts):
    return variables.add_x(model, employees, days, shifts)


@pytest.fixture()
def w(model, employees, days, off_shifts):
    return variables.add_w(model, employees, days, off_shifts)


@pytest.fixture()
def mu(model, competencies, time_periods):
    return variables.add_mu(model, competencies, time_periods)


@pytest.fixture()
def deltas(model, competencies, time_periods):
    return variables.add_deltas(model, competencies, time_periods)


@pytest.fixture()
def lambda_var(model, employees):
    return variables.add_lambda_var(model, employees)


def test_add_minimum_demand(model, employees, competencies, time_periods, min_demand, y, mu):
    constraints.add_minimum_demand(model, y, employees, min_demand, mu, competencies, time_periods)
    model.update()

    assert model.getAttr(GRB.Attr.NumVars) == 12
    assert model.getAttr(GRB.Attr.NumConstrs) == 4


def test_add_maximum_demand(model, employees, competencies, time_periods, min_demand, max_demand, mu):
    constraints.add_maximum_demand(model, max_demand, min_demand, mu, competencies, time_periods)
    model.update()

    assert model.getAttr(GRB.Attr.NumVars) == 4
    assert model.getAttr(GRB.Attr.NumConstrs) == 4


def test_add_deviation_from_ideal_demand(model, min_demand, ideal_demand, mu, deltas, competencies,
                                         time_periods):
    constraints.add_deviation_from_ideal_demand(model, min_demand, ideal_demand, mu, *deltas,
                                                competencies, time_periods)
    model.update()

    assert model.getAttr(GRB.Attr.NumVars) == 12
    assert model.getAttr(GRB.Attr.NumConstrs) == 4


def test_add_maximum_one_allocation_for_each_time(model, competencies, employees, time_periods, y):
    constraints.add_maximum_one_allocation_for_each_time(model, competencies, employees, time_periods, y)
    model.update()

    assert model.getAttr(GRB.Attr.NumVars) == len(competencies) * len(employees) * len(time_periods)
    assert model.getAttr(GRB.Attr.NumConstrs) == len(employees) * len(time_periods)


def test_add_maximum_one_shift_for_each_day(model, employees, days, shifts, x):
    constraints.add_maximum_one_shift_for_each_day(model, employees, days, shifts, x)
    model.update()

    assert model.getAttr(GRB.Attr.NumVars) == len(employees) * len(days) * len(shifts)
    assert model.getAttr(GRB.Attr.NumConstrs) == len(employees) * len(days)


def test_add_mapping_of_shift_to_demand(model, employees, days, shifts, competencies, time_periods, x, y):
    constraints.add_mapping_of_shift_to_demand(model, employees, days, shifts, competencies, time_periods, x, y)
    model.update()

    assert model.getAttr(GRB.Attr.NumVars) == 10
    assert model.getAttr(GRB.Attr.NumConstrs) == 4


@pytest.mark.skip
def test_add_mapping_of_off_shift_to_rest(model, employees, days, off_shifts, competencies, time_periods, w, y):
    constraints.add_mapping_of_off_shift_to_rest(model, employees, days, off_shifts, competencies, time_periods, w, y)
    model.update()

    assert model.getAttr(GRB.Attr.NumVars) == 10
    assert model.getAttr(GRB.Attr.NumConstrs) == 4


def test_add_minimum_weekly_rest(model, employees, days_in_week, weeks, off_shifts, w):
    constraints.add_minimum_weekly_rest(model, employees, days_in_week, weeks, off_shifts, w)
    model.update()

    assert model.getAttr(GRB.Attr.NumVars) == 2
    assert model.getAttr(GRB.Attr.NumConstrs) == 2


def test_add_maximum_contracted_hours(model, competencies, employees, time_periods, weeks, contracted_hours,
                                      y, lambda_var):
    constraints.add_maximum_contracted_hours(model, competencies, employees, time_periods, len(weeks), contracted_hours,
                                             y, lambda_var)
    model.update()

    assert model.getAttr(GRB.Attr.NumVars) == 10
    assert model.getAttr(GRB.Attr.NumConstrs) == 2
