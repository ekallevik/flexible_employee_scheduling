import pytest

from heuristic.criterions.simulated_annealing_criterion import SimulatedAnnealingCriterion
from heuristic.state import State


@pytest.fixture()
def sa():
    return SimulatedAnnealingCriterion(start_temperature=100, end_temperature=1, step=1)


def create_state(objective_function):

    decision_vars = {"x": 0, "y": 0, "w": 0}

    return State(decision_vars, None, None, objective_function, None)

@pytest.mark.parametrize(
    ("start_temperature", "step", "expected_temperature"),
    ([10, 0.9, 9], [10, 0.5, 5], [10, 0.4, 5], [10, 0.99, 9.90]),
)
def test_update_temperature_with_exponential_method(start_temperature, step, expected_temperature):

    criterion = SimulatedAnnealingCriterion(start_temperature, 5, step, method="exponential")

    criterion.update_temperature()

    assert criterion.current_temperature == expected_temperature


@pytest.mark.parametrize(
    ("start_temperature", "step", "expected_temperature"),
    ([10, 1, 9], [10, 5, 5], [10, 6, 5], [10, 0.01, 9.99]),
)
def test_update_temperature_with_linear_method(start_temperature, step, expected_temperature):

    criterion = SimulatedAnnealingCriterion(start_temperature, 5, step, method="linear")

    criterion.update_temperature()

    assert criterion.current_temperature == expected_temperature


@pytest.mark.parametrize(
    ("start_temperature", "end_temperature"), ([0, -50], [50, -50], [-50, -100])
)
def test_create_with_non_positive_temperatures(start_temperature, end_temperature):

    with pytest.raises(ValueError) as e:
        SimulatedAnnealingCriterion(start_temperature, end_temperature, step=1)

    assert str(e.value) == "The temperature must be strictly positive"


def test_create_with_ascending_temperature():

    with pytest.raises(ValueError) as e:
        SimulatedAnnealingCriterion(50, 100, step=1)

    assert str(e.value) == "The start temperature must be greater than the end temperature"


def test_create_with_invalid_method():

    with pytest.raises(ValueError) as e:
        SimulatedAnnealingCriterion(100, 50, step=1, method="invalid")

    assert str(e.value) == "Method: invalid is not a valid choice"


@pytest.mark.parametrize("step", (0, -100))
def test_create_with_non_positive_step(step):

    with pytest.raises(ValueError) as e:
        SimulatedAnnealingCriterion(100, 50, step)

    assert str(e.value) == "The step must be strictly positive"


def test_create_unbounded_growth():

    with pytest.raises(ValueError) as e:
        SimulatedAnnealingCriterion(100, 50, step=1.1, method="exponential")

    assert str(e.value) == "The step must be less than 1 for exponential simulated annealing"


def test_probability_increases_with_objective_value(sa):

    current_state = create_state(100)
    worst_state = create_state(50)
    better_state = create_state(150)

    assert sa.get_probability(worst_state, current_state) < sa.get_probability(better_state, current_state)
