from model.optimality_model import OptimalityModel
from model.optimality_variables import OptimalityVariables


def get_optimality_model(problem):
    return OptimalityModel("test", problem)


def test_get_variables_returns_optimality_variables():

    optimality_model = get_optimality_model("rproblem3_one_week")
    variables = optimality_model.get_variables()

    assert type(variables) == OptimalityVariables
