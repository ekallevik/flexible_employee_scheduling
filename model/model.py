from gurobipy import *

from model.constraints import add_constraints
from model.objective import add_objective
from model.variables import add_variables
from model.sets import get_sets
from model.weights import get_weights


def create_model(name="employee_scheduling"):
    return Model(name=name)


def setup_model(model, find_optimal_solution=True):

    weights = get_weights()
    sets = get_sets()
    variables = add_variables(model, sets)

    add_constraints(model, sets, variables, find_optimal_solution)
    add_objective(model, sets, weights, variables, find_optimal_solution)


def run_model(model):

    # model.write(sys.argv[1] + ".lp")
    # model.setParam("LogFile", (sys.argv[1] + ".log"))
    model.optimize()
    model.write(sys.argv[1] + ".sol")


def main():
    model = create_model()
    setup_model(model, find_optimal_solution=False)
    run_model(model)


if __name__ == "main":
    main()
