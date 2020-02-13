from utils import const

if const.ENVIRONMENT == "local":
    from gurobipy.gurobipy import GRB

def add_y(model, competencies, employees, time_periods):
    return model.addVars(competencies, employees, time_periods, vtype=GRB.BINARY, name='y')


def add_x(model, employees, days, shifts):
    return model.addVars(employees, days, shifts, vtype=GRB.BINARY, name='x')


def add_w(model, employees, days, off_shifts):
    return model.addVars(employees, days, off_shifts, vtype=GRB.BINARY, name='w')


def add_mu(model, competencies, time_periods):
    return model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='mu')


def add_deltas(model, competencies, time_periods):
    deltas = [None, None]
    deltas[0] = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='delta_plus')
    deltas[1] = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='delta_minus')

    return deltas


def add_lambda_var(model, employees):
    return model.addVars(employees, vtype=GRB.BINARY, name="lambda_var")
