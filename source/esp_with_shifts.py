
from gurobipy import *

def add_y_variable(model, competencies, employees, time_periods):
    return model.addVars(competencies, employees, time_periods, vtype=GRB.BINARY, name='y')


def add_mu_variable(model, competencies, time_periods):
    return model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='mu')


def add_delta_variables(model, competencies, time_periods):
    deltas = [None, None]
    deltas[0] = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='delta_plus')
    deltas[1] = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='delta_minus')

    return deltas

# todo: convert min_demand to tupledict
# todo: add competencies
def add_minimum_demand_constraint(model, y, employees, min_demand, mu, competencies, time_periods):

    model.addConstrs((
        quicksum(y[c, e, t] for e in employees)
        == min_demand[c][t] + mu[c, t]
        for c in competencies
        for t in time_periods),
        name='minimum_demand_coverage')

    model.update()


def add_maximum_demand_constraint(model, max_demand, min_demand, mu, competencies, time_periods):

    model.addConstrs((
        mu[c, t] <= max_demand[c][t] - min_demand[c][t]
        for c in competencies
        for t in time_periods),
        name="maximum_demand_coverage"
    )

    model.update()


def add_deviation_from_ideal_demand_constraint(model, min_demand, ideal_demand, mu, delta_plus, delta_minus,
                                               competencies, time_periods):

    model.addConstrs((
        mu[c, t] + min_demand[c][t] - ideal_demand[c][t]
        == delta_plus[c, t] - delta_minus[c, t]
        for c in competencies
        for t in time_periods),
        name="deviation_from_ideal_demand")

    model.update()



