import pytest

from results.converter import Converter
from model.feasibility_model import FeasibilityModel


@pytest.fixture(scope="module")
def gurobi_model():
    gurobi_model = FeasibilityModel(name="test_converter_fixture", problem="rproblem3_one_week")
    gurobi_model.run_model()
    return gurobi_model


@pytest.fixture()
def converter(gurobi_model):
    return Converter(gurobi_model)


def test_get_converted_variables(converter):

    expected_variables = {"x": converter.x, "y": converter.y, "w": converter.w}

    assert converter.get_converted_variables() == expected_variables


def test_convert(gurobi_model, converter):

    variable = converter.gurobi_variables.w

    key_dict = Converter.convert(variable)

    for key1 in key_dict.keys():
        for key2 in key_dict[key1].keys():
            for key3 in key_dict[key1][key2].keys():
                assert key_dict[key1][key2][key3] == variable[key1, key2, key3]


def test_convert_raises_error_on_2d_var(gurobi_model):

    variable = gurobi_model.var.mu

    with pytest.raises(ValueError) as e:
        Converter.convert(variable)

    assert str(e.value) == "This variable is not a 3D dict"
