# from model.hard_constraint_model_class import Optimization_model
# from xml_loader.shift_generation import get_t_covered_by_shift, get_time_periods_in_day, shift_lookup
# from heuristic_calculations import *
from model.feasibility_model import FeasibilityModel
from heuristic_calculations import *
#from pathlib import Path
#import xml.etree.ElementTree as ET
#calculate_partial_weekends, calculate_isolated_working_days, calculate_isolated_off_days, calculate_deviation_from_demand, calculate_f
#from model_class import *
from converter import convert

#problem_name = "rproblem2"
#data_folder = Path(__file__).resolve().parents[1] / 'flexible_employee_scheduling_data/xml data/Real Instances/'
#root = ET.parse(data_folder / (problem_name + '.xml')).getroot()


# t_covered_by_shift = get_t_covered_by_shift(root)
# time_periods_in_day = get_time_periods_in_day(root)
# shift_lookup = shift_lookup(root)








#employee_shifts = {em: [(t,v) for t,v in model.shifts if x[em,t,v] != 0] for em in model.employees}



def main():
    model = FeasibilityModel("esp")
    model.run_model()

    # model = Optimization_model(problem_name)
    # model.add_variables()
    # model.add_constraints()
    # model.set_objective()
    # model.optimize()

    x,y,w = convert(model) 
    model.x = x
    model.y = y
    model.w = w
    # print("############## Deviation from Demand ##############")
    # print(calculate_deviation_from_demand())

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

"""Possibilities now.
1. Could use the same shifts over again. Set random or greedy employees on these shifts
2. Could use the days over again, but use random or greedy shifts and employees
"""
if __name__ == "__main__":
    main()