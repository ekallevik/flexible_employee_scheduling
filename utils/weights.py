
from utils.const import WEEKLY_REST_DURATION


def set_weights():
    """
    Set the objective weights.
    These weights are later weighted relatively and normalized based on problem specific data.
    """
    return {
        "lowest fairness score": 1,
        "demand deviation": 5,
        # Fairness score weights
        "rest": 5,
        "contracted hours": 1,
        "partial weekends": 1,
        "isolated working days": 1,
        "isolated off days": 1,
        "consecutive days": 1,
        "preferences": 1,
    }


def update_relative_weights(weights, num_employees):
    """
    Update weights so that they are relatively weighted against each other.
        * Lowest fairness score:    Multiplied with number of employees to match the accumulated fairness score.
        * Demand deviation:
    """

    weights["lowest fairness score"] *= num_employees
    #weights["demand deviation"]

    return weights


def update_normalized_weights(weights):
    """
    Update weights so that they are normalized.
    """
    # Todo: Implement

    return weights


def get_shift_design_weights():
    return {
        "demand_deviation": 5,
        "shift_duration": 15
    }


def get_weights(staff, time_set):

    num_employees = len(staff["employees"])
    time_step = time_set["step"]
    time_periods = time_set["periods"][0]
    days = time_set["days"]
    weeks = time_set["weeks"]

    weights = set_weights()
    weights = update_relative_weights(weights, num_employees)
    weights = update_normalized_weights(weights)

    return weights

