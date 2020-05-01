import fire

from heuristic.alns import ALNS
from heuristic.criterions.greedy_criterion import GreedyCriterion
from heuristic.state import State
from model.construction_model import ConstructionModel
from model.feasibility_model import FeasibilityModel
from model.optimality_model import OptimalityModel
from model.shift_design_model import ShiftDesignModel
from preprocessing import shift_generation
from results.converter import Converter


def run_shift_design_model(problem="rproblem3", data=None):
    """
    Runs the shift design model.

    :param data: the dataset
    :param problem: the problem instance to run.
    :return: the solved model instance.
    """

    if not data:
        data = shift_generation.load_data(problem)

    original_shifts = data["shifts"]["shifts"]

    sdp = ShiftDesignModel(name="sdp", problem=problem, data=data)
    sdp.run_model()

    used_shifts = sdp.get_used_shifts()
    data["shifts"] = shift_generation.get_updated_shift_sets(problem, data, used_shifts)

    print(f"SDP-reduction from {len(original_shifts)} to {len(used_shifts)} shift")
    percentage_reduction = (len(original_shifts) - len(used_shifts)) / len(original_shifts)
    print(f"This is a reduction of {100*percentage_reduction:.2f}%")

    return data


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


def run_model(model="construction", problem="rproblem3", with_sdp=False):
    """
    Runs the specified model on the given problem.

    :param model: The model version to be run.
    :param problem: the problem instance to run.
    :param with_sdp: Flag to control running of Shift Design Problem
    :return: the solved model instance.
    """

    data = shift_generation.load_data(problem)
    if with_sdp:
        data = run_shift_design_model(problem=problem, data=data)

    if model == "feasibility":
        esp = FeasibilityModel(name="esp_feasibility", problem=problem, data=data)
    elif model == "optimality":
        esp = OptimalityModel(name="esp_optimality", problem=problem, data=data)
    elif model == "construction":
        esp = ConstructionModel(name="esp_construction", problem=problem, data=data)
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
