import pytest

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


def placeholder_func_one():
    """ Placeholder function to use in operator testing """
    return "1"


def placeholder_func_two():
    """ Placeholder function to use in operator testing """
    return "2"


def test_add_destroy_operator(alns):

    alns.add_destroy_operator(placeholder_func_one)
    alns.add_destroy_operator(placeholder_func_two)

    operators = alns.destroy_operators

    assert len(operators.keys()) == 2
    assert operators["placeholder_func_one"] == placeholder_func_one
    assert operators["placeholder_func_two"] == placeholder_func_two


def test_add_repair_operator(alns):

    alns.add_repair_operator(placeholder_func_one)
    alns.add_repair_operator(placeholder_func_two)

    operators = alns.destroy_operators

    assert len(operators.keys()) == 2
    assert operators["placeholder_func_one"] == placeholder_func_one
    assert operators["placeholder_func_two"] == placeholder_func_two


def test_add_operator_with_destroy_argument(alns):

    alns.add_operator(alns.destroy_operators, placeholder_func_one)

    destroy_operators = alns.destroy_operators
    repair_operators = alns.repair_operators

    assert len(destroy_operators.keys()) == 1
    assert len(repair_operators.keys()) == 0
    assert destroy_operators["placeholder_func_one"] == placeholder_func_one
    assert destroy_operators["placeholder_func_one"]() == "1"


def test_add_operator_with_repair_argument(alns):

    alns.add_operator(alns.repair_operators, placeholder_func_one)

    destroy_operators = alns.destroy_operators
    repair_operators = alns.repair_operators

    assert len(destroy_operators.keys()) == 0
    assert len(repair_operators.keys()) == 1
    assert destroy_operators["placeholder_func_one"] == placeholder_func_one
    assert destroy_operators["placeholder_func_one"]() == "1"


