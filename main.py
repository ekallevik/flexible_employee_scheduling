import fire

from model.feasibility_model import FeasibilityModel
from model.optimality_model import OptimalityModel
from model.construction_model import ConstructionModel


def run_model(model="construction", problem="rproblem3"):
    """
    Call this function with (with optional params):
        python main.py run_model MODEL PROBLEM

    :param model: The model version to be run.
    :param problem: the problem instance to run.
    """

    if model == "feasibility":
        esp = FeasibilityModel(name="esp_feasibility", problem=problem)
    elif model == "optimality":
        esp = OptimalityModel(name="esp_optimality", problem=problem)
    elif model == "construction":
        esp = ConstructionModel(name="esp_construction", problem=problem)
    else:
        raise ValueError(f"The model choice: {model} is not valid.")

    esp.run_model()


if __name__ == "__main__":
    fire.Fire()
    run_model()
