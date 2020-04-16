import fire

from heuristic.alns import ALNS
from heuristic.criterions.greedy_criterion import GreedyCriterion
from heuristic.state import State
from model.feasibility_model import FeasibilityModel
from model.optimality_model import OptimalityModel
from model.construction_model import ConstructionModel
from model.shift_design_model import ShiftDesignModel
from results.converter import Converter


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
    state = State(converted_solution)

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
    run_shift_design_model()