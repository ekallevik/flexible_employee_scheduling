import fire

from model.feasibility_model import FeasibilityModel
from model.optimality_model import OptimalityModel


def run_model(model="feasibility", problem="rproblem2"):
    """
    Call this function with (with optional params):
        python main.py run_model MODEL PROBLEM

    :param model: The model version to be run.
    :param problem: the problem instance to run.
    """

    if model == "feasibility":
        esp = FeasibilityModel(name="esp_feasibility", problem=problem)
    elif model == "optimality":
        esp = OptimalityModel(name="esp", problem="rproblem2")
    else:
        raise ValueError(f"The model choice: {model} is not valid.")

    esp.run_model()


if __name__ == "__main__":
    fire.Fire()
