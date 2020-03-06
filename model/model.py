from gurobipy import *

import model.constraints
import model.objective as objective
import model.sets as sets
import model.variables as variables
import model.weights as weights



def create_model(name="employee_scheduling"):
    return Model(name=name)


def setup_model(model, find_optimal_solution=True):
    weights = we.get_weights()
    sets = sets.get_sets()
    variables = add_variables(model, sets)

    add_constraints(model, sets, variables, find_optimal_solution)
    objective.add_objective(model, sets, weights, variables, find_optimal_solution)


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
