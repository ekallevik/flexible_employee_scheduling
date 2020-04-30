
from utils.const import WEEKLY_REST_DURATION, DEFAULT_CONTRACTED_HOURS
from gurobipy.gurobipy import tupledict


def get_shift_design_weights():
    return {
        "demand_deviation": 5,
        "shift_duration": 15
    }


def set_weights():
    """
    Fairness aspects are translated into how many hours of demand deviation that is accepted to satisfy the respective
    fairness aspect. In addition, the weight of the least favoured employee fairness score is set.
    """

    return{
        # Weight of fairness aspects. Rest, contracted hours and preferences should be treated as hours.
        "rest": 0,
        "contracted hours": 0,
        "partial weekends": 8,
        "isolated working days": 0,
        "isolated off days": 0,
        "consecutive days": 0,
        "preferences": 0,

        # Weight of least favored employee. Use interval [0, 1].for
        "lowest fairness score": 0.5,
    }


def get_weights(time_set, staff):
    """
    Weights are relatively weighted and translated into hours if needed.
    """

    weights = set_weights()
    weights = add_demand_deviation_weight(weights)
    weights = scale_weights_to_hours(weights, time_set)
    weights = scale_weights_relatively(weights, staff)

    return weights


def add_demand_deviation_weight(weights):

    weights["demand deviation"] = 1

    return weights


def scale_weights_to_hours(weights, time_set):

    time_step = time_set["step"]

    # Demand deviation, contracted hours and preferences needs to be scaled to hours
    weights["demand deviation"] *= time_step
    weights["contracted hours"] *= time_step
    weights["preferences"] *= time_step

    return weights


def scale_weights_relatively(weights, staff):

    num_employees = len(staff["employees"])
    employee_contracted_hours = staff["employee_contracted_hours"]

    weights = scale_contracted_hours_relatively(weights, employee_contracted_hours)
    weights = scale_least_favoured_employee(weights, num_employees)
    weights = scale_demand_deviation(weights, num_employees)

    return weights


def scale_contracted_hours_relatively(weights, employee_contracted_hours):
    """
    Contracted hours weight is scaled for each employee based on the ratio between contracted hours and
    default contracted hours.
    """

    contracted_hours_weights = tupledict()

    for e in employee_contracted_hours:
        contracted_hours_weights[e] = weights["contracted hours"] * \
                                      (DEFAULT_CONTRACTED_HOURS / employee_contracted_hours[e])

    weights["contracted hours"] = contracted_hours_weights

    return weights


def scale_least_favoured_employee(weights, num_employees):
    """ Scale the fairness score ot the least favored employee relatively to the accumulated fairness score """

    weights["lowest fairness score"] *= num_employees

    return weights


def scale_demand_deviation(weights, num_employees):
    """ Scale the demand deviation proportional to the two different fairness score terms """

    weights["demand deviation"] *= num_employees

    return weights











def get_weights_old():
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



#def get_weights(staff, time_set):

    weights = set_weights()
    weights = update_relative_weights(weights, staff)
    weights = update_normalized_weights(weights, staff, time_set)

    return weights

