from model.base_variables import BaseVariables
from model.construction_model import ConstructionModel


def get_construction_model(problem):
    return ConstructionModel("test", problem)


def test_get_variables_returns_base_variables():

    construction_model = get_construction_model("rproblem3_one_week")
    variables = construction_model.get_variables()

    assert type(variables) == BaseVariables
