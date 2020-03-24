from model.feasibility_model import FeasibilityModel
from heuristic_calculations import *
from repair_algorithms import *
from destroy_algorithms import *
#calculate_partial_weekends, calculate_isolated_working_days, calculate_isolated_off_days, calculate_deviation_from_demand, calculate_f
#from model_class import *
from converter import convert




#employee_shifts = {em: [(t,v) for t,v in model.shifts if x[em,t,v] != 0] for em in model.employees}



def main():
    model = FeasibilityModel("esp")
    model.run_model()

    x,y,w = convert(model) 
    model.x = x
    model.y = y
    model.w = w
    print("############## Deviation from Demand ##############")
    print(calculate_deviation_from_demand(model))

    print("############## Partial Weekends ##############")
    print(calculate_partial_weekends(model))

    print("############## Isolated Working Days ##############")
    print(calculate_isolated_working_days(model))

    print("############## Isolated Off Days ##############")
    print(calculate_isolated_off_days(model))

    print("############## Consecutive Working Days ##############")
    print(calculate_consecutive_days(model))

    print("############## Employees F ##############")
    print(calculate_f(model))

    print("############## Objective Function ##############")
    print(calculate_objective_function(model))

    partial = remove_partial_weekends(model)
    add_random_weekends(model, partial)
    add_greedy_weekends(model, partial)

    iso = remove_isolated_working_day(model)
    add_previously_isolated_days_randomly(model, iso)
    add_previously_isolated_days_greedy(model, iso)
    print(calculate_objective_function(model))


"""Possibilities now.
1. Could use the same shifts over again. Set random or greedy employees on these shifts
2. Could use the days over again, but use random or greedy shifts and employees
"""
if __name__ == "__main__":
    main()