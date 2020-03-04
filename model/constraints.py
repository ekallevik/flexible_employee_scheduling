from gurobipy import *


def add_y(model, sets):
    return model.addVars(sets["competencies"], sets["employees"]["all"], sets["time"]["periods"], vtype=GRB.BINARY, name='y')

def add_x(model, sets):
    return model.addVars(sets["employees"]["all"], sets["shifts"]["shifts"], vtype=GRB.BINARY, name='x')

