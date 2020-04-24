import fire

from heuristic.alns import ALNS
from heuristic.criterions.greedy_criterion import GreedyCriterion
from heuristic.state import State
from model.feasibility_model import FeasibilityModel
from model.optimality_model import OptimalityModel
from model.construction_model import ConstructionModel
from model.shift_design_model import ShiftDesignModel
from results.converter import Converter
from heuristic.heuristic_calculations import *

def run_shift_design_model(problem="rproblem3"):
    """
    Runs the shift design model.

    :param problem: the problem instance to run.
    :return: the solved model instance.
    """

    sdp = ShiftDesignModel(name="sdp", problem=problem)
    sdp.run_model()

    return sdp


def run_heuristic(construction_model="feasibility", problem="rproblem2"):
    """
    Non-complete skeleton for running ALNS.

    :param construction_model: the model to be use to construct the initial solution.
    :param problem: the problem instance to run.
    :return:
    """

    candidate_solution = run_model(model=construction_model, problem=problem)

    converter = Converter(candidate_solution)
    converted_solution = converter.get_converted_variables()
    
    #The soft variables, hard variables objective function and f is needed to do delta calculations later on.
    # These calculations are done using heuristic calculations on the solution gotten from the construction model.
    # This is why they are needed to be calculated here and placed in the initial state at the beginning. 
    soft_variables = {
        "negative_deviation_from_demand": calculate_negative_deviation_from_demand(candidate_solution, converted_solution["y"]),
        "partial_weekends": calculate_partial_weekends(candidate_solution, converted_solution["x"]),
        "consecutive_days": calculate_consecutive_days(candidate_solution, converted_solution["x"]),
        "isolated_off_days": calculate_isolated_off_days(candidate_solution, converted_solution["x"]),
        "isolated_working_days": calculate_isolated_working_days(candidate_solution, converted_solution["x"]),
        "deviation_contracted_hours": calculate_negative_deviation_from_contracted_hours(candidate_solution, converted_solution["y"])
    }

    hard_variables = {
        "below_minimum_demand": {},
        "above_maximum_demand": {},
        "more_than_one_shift_per_day": {},
        "cover_multiple_demand_periods": {},
        "weekly_off_shift_error": {},
        "no_work_during_off_shift": {},
        "mapping_shift_to_demand": {},
        "delta_positive_contracted_hours": {}
    }
    objective_function, f = calculate_objective_function(model, soft_variables)

    state = State(converted_solution, soft_variables, hard_variables, objective_function, f)

    criterion = GreedyCriterion()

    alns = ALNS(state, criterion)
    solution = alns.iterate(iterations=1000)


def run_model(model="construction", problem="rproblem3"):
    """
    Runs the specified model on the given problem.

    :param model: The model version to be run.
    :param problem: the problem instance to run.
    :return: the solved model instance.
    """

    if model == "feasibility":
        esp = FeasibilityModel(name="esp_feasibility", problem=problem)
    elif model == "optimality":
        esp = OptimalityModel(name="esp_optimality", problem=problem)
    elif model == "construction":
        esp = ConstructionModel(name="esp_construction", problem=problem)
    else:
        raise ValueError(f"The model choice '{model}' is not valid.")

    esp.run_model()

    return esp


if __name__ == "__main__":
    """ 
    Run any function by using:
        python main.py FUNCTION_NAME *ARGS
    """
    fire.Fire()
