import pytest
import numpy as np

from heuristic.alns import ALNS
from heuristic.state import State


@pytest.fixture()
def var():
    """ Placeholder fixture until a better solution is implemented """
    return {"x": None, "y": None, "w": None}


@pytest.fixture()
def state(var):
    """ Placeholder fixture until a better solution is implemented """
    return State(var)


@pytest.fixture()
def alns(state):
    """ Placeholder fixture until a better solution is implemented """
    return ALNS(state)


def func_one():
    """ Placeholder function to use in operator testing """
    return "1"


def func_two():
    """ Placeholder function to use in operator testing """
    return "2"


def test_select_operator(alns):

    alns.add_destroy_operator(func_one)
    alns.add_destroy_operator(func_two)
    alns.initialize_destroy_weights()
    selected_operator = alns.select_operator(alns.destroy_operators, alns.destroy_weights)

    assert selected_operator[0] in alns.destroy_operators.keys()
    assert selected_operator[1] == selected_operator.__name__


@pytest.mark.parametrize("weights, expected", [
    ({"first": 1.0, "second": 1.0}, [0.5, 0.5]),
    ({"first": 3.0, "second": 1.0}, [0.75, 0.25]),
    ({"first": 0.6, "second": 0.2}, [0.75, 0.25]),
    ({"first": 999, "second": 1}, [0.999, 0.001]),
])
def test_get_probabilities(alns, weights, expected):

    assert alns.get_probabilities(weights) == pytest.approx(expected)


def test_add_destroy_operator(alns):

    alns.add_destroy_operator(func_one)
    alns.add_destroy_operator(func_two)

    assert alns.destroy_operators == {"func_one": func_one, "func_two": func_two}
    assert alns.repair_operators == {}


def test_add_repair_operator(alns):

    alns.add_repair_operator(func_one)
    alns.add_repair_operator(func_two)

    assert alns.destroy_operators == {}
    assert alns.repair_operators == {"func_one": func_one, "func_two": func_two}


def test_add_operator_with_destroy_argument(alns):

    alns.add_operator(alns.destroy_operators, func_one)

    assert alns.destroy_operators == {"func_one": func_one}
    assert alns.repair_operators == {}
    assert alns.destroy_operators["func_one"]() == "1"


def test_add_operator_with_repair_argument(alns):

    alns.add_operator(alns.repair_operators, func_one)

    assert alns.destroy_operators == {}
    assert alns.repair_operators == {"func_one": func_one}
    assert alns.repair_operators["func_one"]() == "1"


@pytest.mark.parametrize("variable", ["string", ["list"], {"dict": "value"}])
def test_add_operator_without_function_raises_error(alns, variable):

    with pytest.raises(ValueError):
        alns.add_operator(alns.destroy_operators, variable)


def test_initialize_destroy_weights(alns):

    alns.add_destroy_operator(func_one)
    alns.add_destroy_operator(func_two)

    alns.initialize_destroy_weights()

    assert alns.destroy_weights == {"func_one": 1, "func_two": 1}


def test_initialize_destroy_weights_raises_error_on_no_operators(alns):

    with pytest.raises(ValueError):
        alns.initialize_destroy_weights()


def test_initialize_repair_weights(alns):

    alns.add_repair_operator(func_one)
    alns.add_repair_operator(func_two)

    alns.initialize_repair_weights()

    assert alns.repair_weights == {"func_one": 1, "func_two": 1}


def test_initialize_repair_weights_raises_error_on_no_operators(alns):

    with pytest.raises(ValueError):
        alns.initialize_repair_weights()
