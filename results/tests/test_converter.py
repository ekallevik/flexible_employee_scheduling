import pytest

from results.converter import Converter
from model.feasibility_model import FeasibilityModel


@pytest.fixture()
def gurobi_model():
    gurobi_model = FeasibilityModel(name="test_converter_fixture", problem="rproblem2")
    gurobi_model.run_model()
    return gurobi_model


@pytest.fixture()
def converter(gurobi_model):
    return Converter(gurobi_model)


def test_get_converted_variables(converter):

    expected_variables = {"x": converter.x, "y": converter.y, "w": converter.w}

    assert converter.get_converted_variables() == expected_variables


def test_convert_x(gurobi_model, converter):

    assert type(converter.x) == dict
    assert len(converter.x) == len(gurobi_model.var.x)
    assert not any(value < 0 for value in converter.x.values())


def test_convert_y(gurobi_model, converter):

    assert type(converter.y) == dict
    assert len(converter.y) == len(gurobi_model.var.y)
    assert not any(value < 0 for value in converter.y.values())


def test_convert_w(gurobi_model, converter):

    assert type(converter.w) == dict
    assert len(converter.w) == len(gurobi_model.var.w)
    assert not any(value < 0 for value in converter.w.values())
