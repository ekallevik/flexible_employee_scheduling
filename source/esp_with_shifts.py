
from gurobipy import *

def add_y_variable(model, competencies, employees, time_periods):
    return model.addVars(competencies, employees, time_periods, vtype=GRB.BINARY, name='y')


def add_mu_variable(model, competencies, time_periods):
    return model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='mu')


def add_minimum_demand_constraint(model, y, employees, min_demand, mu, competencies, time_periods):

    model.addConstrs((
        quicksum(y[c, e, t] for e in employees)
        == min_demand[c][t] + mu[c, t]
        for c in competencies
        for t in time_periods),
        name='minimum_demand_coverage')

    model.update()


