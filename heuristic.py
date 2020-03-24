from model.hard_constraint_model_class import Optimization_model
from xml_loader.shift_generation import get_t_covered_by_shift, get_time_periods_in_day, shift_lookup
from heuristic_calculations import *
from pathlib import Path
import xml.etree.ElementTree as ET
#calculate_partial_weekends, calculate_isolated_working_days, calculate_isolated_off_days, calculate_deviation_from_demand, calculate_f
#from model_class import *
from converter import convert

problem_name = "rproblem2"
data_folder = Path(__file__).resolve().parents[1] / 'flexible_employee_scheduling_data/xml data/Real Instances/'
root = ET.parse(data_folder / (problem_name + '.xml')).getroot()


t_covered_by_shift = get_t_covered_by_shift(root)
time_periods_in_day = get_time_periods_in_day(root)
shift_lookup = shift_lookup(root)








#employee_shifts = {em: [(t,v) for t,v in model.shifts if x[em,t,v] != 0] for em in model.employees}



def main():
    model = Optimization_model(problem_name)
    model.add_variables()
    model.add_constraints()
    model.set_objective()
    model.optimize()
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

main()
# partial = remove_partial_weekends()
# add_greedy_weekends(partial)

# iso = remove_isolated_working_day()
# add_previously_isolated_days_greedy(iso)

# print(calculate_objective_function())
# iso_w = calculate_isolated_working_days()
# # iso_off = calculate_isolated_off_days()
# iso_w_days = [key for key, value in iso_w.items() if value != 0]
# print(iso_w_days)

# print(calculate_objective_function())

# print(calculate_objective_function())
# iso_w = calculate_isolated_working_days()
# iso_off = calculate_isolated_off_days()
# iso_w_days = [key for key, value in iso_w.items() if value != 0]
# iso_off_days = [key for key, value in iso_off.items() if value != 0]
# print(iso_w_days)
#print(iso_off_days)
#print([(7,i) for i in model.days for t,v in model.shifts_at_day[i] if x[7,t,v] == 1])

#print("----------------------------------")
#print([(e,t,v) for e,t,v in w if w[e,t,v] == 1])




# def remove_partial_weekends():
#     partial_weekend_shifts = calculate_partial_weekends()[1]
#     for day in partial_weekend_shifts:
#         if(day in model.saturdays):
#             for shift in partial_weekend_shifts[day]:
#                 if(len(partial_weekend_shifts[day+1]) != 0):
#                     set_x(shift[0], shift[1], shift[2], 0)
#                     employee_next_day = partial_weekend_shifts[day+1].pop(0)
#                     set_x(employee_next_day, shift[1], shift[2], 1)

#         else:
            



0# def remove_partial_weekends():
#     partial_weekends = calculate_partial_weekends()
#     actual_partial_weekends = [key for key, value in partial_weekends.items() if value != 0]
#     partial_weekend_shifts = {}

#     for e,i in actual_partial_weekends:
#         partial_weekend_shifts[e,i] = []
#         for shift in employee_shifts[e]:
#             if shift[0] >= 24*i and shift[0] <= 24*(i+2):
#                 partial_weekend_shifts[e,i].append(shift)
#     print(partial_weekend_shifts)



    # first_half = int(len(actual_partial_weekends)/2)
    # for s in range(first_half):
    #     print(s)
    #     e,i = actual_partial_weekends[s]
    #     for shift in employee_shifts[e]:
    #         if shift[0] >= 24*i and shift[0] <= 24*(i+2):
    #             set_x(e,shift[0], shift[1], 0)

    # for s in range(first_half,len(actual_partial_weekends)):
    #     print(actual_partial_weekends[s])
        

    #print(actual_partial_weekends)

#print(calculate_partial_weekends()[1])


#print(calculate_objective_function())


#print(calculate_objective_function())

# cover_minimum_demand()
# under_maximum_demand()
# maximum_one_shift_per_day()
# cover_only_one_demand_per_time_period()
# one_weekly_off_shift()
# no_work_during_off_shift()
# mapping_shift_to_demand()

# no_work_during_off_shift()
#calculate_objective_function()

