
from gurobipy import *


from source.esp_with_shifts import add_minimum_demand_constraint, add_y_variable, add_mu_variable


def test_add_minimum_demand_constraint():

    model = Model("employee_scheduling_with_shifts")

    employees = [1, 2]
    min_demand = {"comp1": [1, 0], "comp2": [0, 1]}
    competencies = ["comp1", "comp2"]
    time_periods = [0, 1]

    y = add_y_variable(model, competencies, employees, time_periods)
    mu = add_mu_variable(model, competencies, time_periods)

    add_minimum_demand_constraint(model, y, employees, min_demand, mu, competencies, time_periods)

    assert model.getAttr(GRB.Attr.NumVars) == 12
    assert model.getAttr(GRB.Attr.NumConstrs) == 4



def test_add_minimum_demand_constaint_with_competencies():
    pass