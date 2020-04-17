from model.model_class import Optimization_model
from model.hard_constraint_model_class import Optimization_model as Feasibility_model
from heuristic.heuristic_calculations import calculate_objective_function as calc_ob
from heuristic.destroy_algorithms import remove_partial_weekends, remove_isolated_working_day
from heuristic.repair_algorithms import *
from heuristic.state import State 
from heuristic.alns_calculator import Alns_calculator
from heuristic.converter import convert
from heuristic.alns import ALNS
from heuristic.heuristic_calculations import *
import cProfile
import pstats
from visualisation.solution_visualizer import Visualizer


#employee_shifts = {em: [(t,v) for t,v in model.shifts if x[em,t,v] != 0] for em in model.employees}



def main():
    problem_name = "rproblem3" 
    model = Feasibility_model(problem_name)
    model.add_variables()
    model.add_constraints()
    model.set_objective()
    model.optimize()
    x,y,w = convert(model) 

    #visualizer = Visualizer(problem_name)
    #visualizer.create_gantt_chart()



    #calculator = Alns_calculator(model)
    soft_variables = {
        "negative_deviation_from_demand": calculate_negative_deviation_from_demand(model, y),
        "partial_weekends": calculate_partial_weekends(model, x),
        "consecutive_days": calculate_consecutive_days(model, x),
        "isolated_off_days": calculate_isolated_off_days(model, x),
        "isolated_working_days": calculate_isolated_working_days(model, x),
        "deviation_contracted_hours": calculate_negative_deviation_from_contracted_hours(model, y)
    }

    hard_vars = {
        "below_minimum_demand": {},
        "above_maximum_demand": {},
        "more_than_one_shift_per_day": {},
        "cover_multiple_demand_periods": {},
        "weekly_off_shift_error": {},
        "no_work_during_off_shift": {},
        "mapping_shift_to_demand": {},
        "delta_positive_contracted_hours": calculate_positive_deviation_from_contracted_hours(model, y)
    }

    objective_function, f = calc_ob(model, soft_variables)
    #print(soft_variables["partial_weekends"])

    initial_state = State({"x": x, "y":y, "w":w}, soft_variables, hard_vars, objective_function, f)
    
    alns = ALNS(initial_state, model)
    alns.iterate(1)
    
    model.x = x
    model.y = y
    model.w = w
    #print(calculate_objective_function(model))

    # print("############## Deviation from Demand ##############")
    # print(calculate_deviation_from_demand(model))

    # print(calculate_negative_deviation_from_contracted_hours(model))
    # print(calculate_positive_deviation_from_contracted_hours(model))

    # print("############## Partial Weekends ##############")
    # print(calculate_partial_weekends(model))

    # print("############## Isolated Working Days ##############")
    # print(calculate_isolated_working_days(model))

    # print("############## Isolated Off Days ##############")
    # print(calculate_isolated_off_days(model))

    # print("############## Consecutive Working Days ##############")
    # print(calculate_consecutive_days(model))

    # print("############## Employees F ##############")
    # print(calculate_f(model))

    #print("############## Objective Function ##############")
    #print(calculate_objective_function(model))

    # remove_partial_weekends(model)
    # iso_days = remove_isolated_working_day(model)
    # add_previously_isolated_days_randomly(model, iso_days)
    # add_previously_isolated_days_greedy(model, iso_days)

    # partial = remove_partial_weekends(model)
    # add_random_weekends(model, partial)
    # add_greedy_weekends(model, partial)

"""Possibilities now.
1. Could use the same shifts over again. Set random or greedy employees on these shifts
2. Could use the days over again, but use random or greedy shifts and employees
"""
cProfile.run('main()', 'stats')
p = pstats.Stats('stats')
p.strip_dirs().sort_stats('time').print_stats(15)
#main()
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

