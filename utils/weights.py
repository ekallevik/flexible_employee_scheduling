
from utils.const import WEEKLY_REST_DURATION
from gurobipy.gurobipy import tupledict


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


def update_relative_weights(weights, staff):
    """
    Update weights so that they are relatively weighted against each other.
        * Lowest fairness score:    Multiplied with number of employees to match the accumulated fairness score.
        * Demand deviation:
    """

    num_employees = len(staff["employees"])

    weights["lowest fairness score"] *= num_employees
    #weights["demand deviation"]

    return weights


def normalize_weekly_rest_weight(weights):

    max_additional_weekly_rest = WEEKLY_REST_DURATION[1] - WEEKLY_REST_DURATION[0]
    weights["rest"] /= max_additional_weekly_rest

    return weights


def normalize_contracted_hours_weight(weights, employee_contracted_hours, num_weeks):

    contracted_hours_weights = tupledict()
    normalized_deviation_percentage = 0.05

    for e in employee_contracted_hours:
        contracted_hours_weights[e] = weights["contracted hours"] / \
                                      (num_weeks * employee_contracted_hours[e] * normalized_deviation_percentage)

    weights["contracted hours"] = contracted_hours_weights

    return weights


def update_normalized_weights(weights, staff, time_set):
    """
    Update weights so that they are normalized to around 1.
    Weekly rest
    """
    employee_contracted_hours = staff["employee_contracted_hours"]
    num_weeks = len(time_set["weeks"])

    weights = normalize_weekly_rest_weight(weights)
    weights = normalize_contracted_hours_weight(weights, employee_contracted_hours, num_weeks)

    return weights


def get_shift_design_weights():
    return {
        "demand_deviation": 5,
        "shift_duration": 15
    }


def get_weights(staff, time_set):

    weights = set_weights()
    weights = update_relative_weights(weights, staff)
    weights = update_normalized_weights(weights, staff, time_set)
    print(weights["contracted hours"][1])

    return weights

