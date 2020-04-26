from model.model_class import Optimization_model
from model.hard_constraint_model_class import Optimization_model as Feasibility_model
from heuristic.heuristic_calculations import calculate_objective_function as calc_ob
from heuristic.criterions.greedy_criterion import GreedyCriterion
from heuristic.criterions.simulated_annealing_criterion import SimulatedAnnealingCriterion
from heuristic.state import State 
from heuristic.alns_calculator import Alns_calculator
from heuristic.converter import convert
from heuristic.alns import ALNS
from heuristic.heuristic_calculations import *
import cProfile
import pstats


def main():
    problem_name = "rproblem2" 
    model = Feasibility_model(problem_name)
    model.add_variables()
    model.add_constraints()
    model.set_objective()
    model.optimize()
    #model.model.write("solution_files/optimality_model_rproblem3.sol")
    x,y,w = convert(model) 



    soft_variables = {
        "deviation_from_ideal_demand": calculate_deviation_from_demand(model, y),
        "partial_weekends": calculate_partial_weekends(model, x),
        "consecutive_days": calculate_consecutive_days(model, x),
        "isolated_off_days": calculate_isolated_off_days(model, x),
        "isolated_working_days": calculate_isolated_working_days(model, x),
        "contracted_hours": calculate_negative_deviation_from_contracted_hours(model, y)
    }
    hard_vars = {
        "below_minimum_demand": {(c,t): 0 for c in model.competencies for t in model.time_periods},
        "above_maximum_demand": {(c,t): 0 for c in model.competencies for t in model.time_periods},
        "more_than_one_shift_per_day": {(e,i): 0 for e in model.employees for i in model.days},
        "cover_multiple_demand_periods": {(e,t): 0 for e in model.employees for t in model.time_periods},
        "weekly_off_shift_error": {(e,j): 0 for e in model.employees for j in model.weeks},
        #"no_work_during_off_shift": {},
        "mapping_shift_to_demand": {(c,t): 0 for c in model.competencies for t in model.time_periods},
        "delta_positive_contracted_hours": {e: 0 for e in model.employees}
    }

    calculate_weekly_rest(model, x, w)
    objective_function, f = calc_ob(model, soft_variables, w)

    initial_state = State({"x": x, "y":y, "w":w}, soft_variables, hard_vars, objective_function, f)
    #initial_state.write("optimality_model_rproblem3_heuristic_rest")
    #simulated_annealing_criterion = SimulatedAnnealingCriterion()
    greedy_criterion = GreedyCriterion()
    alns = ALNS(initial_state, model, greedy_criterion)
    alns.iterate(10)


"""Possibilities now.
1. Could use the same shifts over again. Set random or greedy employees on these shifts
2. Could use the days over again, but use random or greedy shifts and employees
"""
cProfile.run('main()', 'stats')
p = pstats.Stats('stats')
p.strip_dirs().sort_stats('time').print_stats(20)
