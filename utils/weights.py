
from utils.const import DEFAULT_CONTRACTED_HOURS
from gurobipy.gurobipy import tupledict

# Set weighting of Optimality Model

def set_weights():
    """
    Fairness aspects are translated into how many hours of demand deviation that is accepted to satisfy the respective
    fairness aspect. In addition, both the weight of the least favoured employee fairness score and the scaling between
    excess and deficit demand is set. The latter makes it possible to increase or decrease the impact of either
    over- or under staffing.
    """

    return{
        # Weight of fairness aspects. Rest, contracted hours and preferences should be treated as hours.
        "rest": 20,
        "contracted hours": 2,
        "partial weekends": 8,
        "isolated working days": 10,
        "isolated off days": 10,
        "consecutive days": 12,
        "preferences": 1.5,

        # Weight of least favored employee. Use interval [0, 1].
        "lowest fairness score": 0.5,

        # Scaling excess and deficit of demand
        "excess demand deviation factor": 1.0,
        "deficit demand deviation factor": 1.0,
    }


# Weighting of Shift Design Model

def get_shift_design_weights():
    return {
        "demand_deviation": 5,
        "shift_duration": 15,

        # Scaling excess and deficit of demand
        "excess demand deviation factor": 1.0,
        "deficit demand deviation factor": 1.0,

    }


def get_weights(time_set, staff):
    """
    The reference weight of demand deviation is added. Then the weights are scaled to hours, which is the reference
    time step. Lastly, the weights are scaled relatively to each other and to the problem specific data.
    """

    weights = set_weights()
    weights = correct_weights(weights)
    weights = add_demand_deviation_weight(weights)
    weights = scale_weights_to_hours(weights, time_set)
    weights = scale_weights_relatively(weights, staff)
    weights = scale_up_weights(weights, staff)

    return weights


def correct_weights(weights):
    """
    Weekly rest contributes positively to the fairness score (if additional hours are granted), different from the
    other fairness aspects. Thus it is necessary to correct the weight, so that it actually represents the intention
    defined in set_weights.

    NOTE:   Preferences are also contributing positively to the fairness score, but these respective weights are
            corrected naturally in the generate_preferences-function.
    """

    weights["rest"] = 1 / weights["rest"]

    return weights


def add_demand_deviation_weight(weights):
    """
    Weight of demand deviation is not an input value and is thus treated in a separate function. The weight is set
    to 1, serving as the reference value for remaining weights. This value should not be changed.
    """

    weights["demand deviation"] = 1

    return weights


def scale_weights_to_hours(weights, time_set):
    """
    Demand deviation, contracted hours and preferences needs to be scaled to hours, as this is the reference time step.
    """

    time_step = time_set["step"]

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
    default contracted hours. Scaling factor allows for
    """

    contracted_hours_weights = tupledict()
    scaling_factor = 1.0

    for e in employee_contracted_hours:
        contracted_hours_weights[e] = scaling_factor * weights["contracted hours"] * \
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


def scale_up_weights(weights, staff):

    employees = staff["employees"]
    scaling_factor = 1

    weights["demand deviation"] *= scaling_factor
    weights["rest"] *= scaling_factor
    weights["partial weekends"] *= scaling_factor
    weights["isolated working days"] *= scaling_factor
    weights["isolated off days"] *= scaling_factor
    weights["consecutive days"] *= scaling_factor
    weights["preferences"] *= scaling_factor

    for e in employees:
        weights["contracted hours"][e] *= scaling_factor

    return weights








