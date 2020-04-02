from model.base_variables import BaseVariables
from model.feasibility_model import FeasibilityModel


def get_feasibility_model(problem):
    return FeasibilityModel("test", problem)


def test_get_variables_returns_feasibility_model():

    feasibility_model = get_feasibility_model("rproblem3_one_week")
    variables = feasibility_model.get_variables()

    assert type(variables) == BaseVariables
