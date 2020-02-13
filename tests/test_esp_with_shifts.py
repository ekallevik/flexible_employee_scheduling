import pytest
from gurobipy import *


from source.esp_with_shifts import add_minimum_demand_constraint, add_y_variable, add_mu_variable, \
    add_maximum_demand_constraint, add_deviation_from_ideal_demand_constraint, add_delta_variables


@pytest.fixture()
def model():
    return Model("employee_scheduling_with_shifts")

@pytest.fixture()
def employees():
    return [0, 1]


@pytest.fixture()
def competencies():
    return ["comp1", "comp2"]


@pytest.fixture()
def time_periods():
    return [0, 1]


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
    return add_y_variable(model, competencies, employees, time_periods)


@pytest.fixture()
def mu(model, competencies, time_periods):
    return add_mu_variable(model, competencies, time_periods)


@pytest.fixture()
def deltas(model, competencies, time_periods):
    return add_delta_variables(model, competencies, time_periods)

def test_add_minimum_demand_constraint(model, employees, competencies, time_periods, min_demand, y, mu):


    add_minimum_demand_constraint(model, y, employees, min_demand, mu, competencies, time_periods)

    assert model.getAttr(GRB.Attr.NumVars) == 12
    assert model.getAttr(GRB.Attr.NumConstrs) == 4


def test_add_maximum_demand_constraint(model, employees, competencies, time_periods, min_demand, max_demand, mu):

    add_maximum_demand_constraint(model, max_demand, min_demand, mu, competencies, time_periods)

    assert model.getAttr(GRB.Attr.NumVars) == 4
    assert model.getAttr(GRB.Attr.NumConstrs) == 4
    

def test_add_deviation_from_ideal_demand_constraint(model, min_demand, ideal_demand, mu, deltas, competencies, time_periods):

    add_deviation_from_ideal_demand_constraint(model, min_demand, ideal_demand, mu, *deltas,
                                               competencies, time_periods)

    print(model.getConstrs())

    assert True