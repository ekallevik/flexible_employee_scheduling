from gurobipy import *

from model.constraints import add_constraints
from model.sets import get_sets
from model.variables import add_variables
from model.weights import get_weights


def create_model(name="employee_scheduling"):
    return Model(name=name)


def setup_model(model):

    weights = get_weights()
    sets = get_sets()
    variables = add_variables(model, sets)

    add_constraints(model, sets, variables, weights)

    #todo: add objective-function somewhere


