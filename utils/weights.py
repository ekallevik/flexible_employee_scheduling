from pprint import pprint

from utils.const import DEFAULT_CONTRACTED_HOURS
from gurobipy.gurobipy import tupledict

# Set weighting of Optimality Model


def set_weights():
    """
    Fairness aspects are translated into how many hours of demand deviation that is accepted to
    satisfy the respective fairness aspect. In addition, both the weight of the least favoured
    employee fairness score and the scaling between excess and deficit demand is set. The latter
    makes it possible to increase or decrease the impact of either over- or under staffing.
    """

    return{
        # Weight of fairness aspects. Rest, contracted hours and preferences should be treated as hours.
        "rest": 0.5,
        "contracted hours": 1,
        "partial weekends": 8,
        "isolated working days": 10,
        "isolated off days": 10,
        "consecutive days": 12,
        "preferences": 5,
        # Weight of least favored employee. Use interval [0, 1].
        "lowest fairness score": 0.1,
        # Scaling excess and deficit of demand
        "excess demand deviation factor": 1.0,
        "deficit demand deviation factor": 1.0,
    }


def set_shift_design_weights():
    return {
        "use of short shift": 5,
        "use of long shift": 5,
        # Scaling excess and deficit of demand
        "excess demand deviation factor": 1.0,
        "deficit demand deviation factor": 1.0,
    }


def get_shift_design_weights(time_set):

    weights = set_shift_design_weights()

    # Scale weights to hours
    weights["excess demand deviation factor"] = scale_weight_to_hours(
        weights["excess demand deviation factor"], time_set["step"]
    )
    weights["deficit demand deviation factor"] = scale_weight_to_hours(
        weights["deficit demand deviation factor"], time_set["step"]
    )

    return weights


def get_weights(time_set, staff):
    """
    The reference weight of demand deviation is added. Then the weights are scaled to hours,
    which is the reference time step. Lastly, the weights are scaled relatively to each other and
    to the problem specific data.
    """

    weights = set_weights()

    # Scale preferences to number of weeks
    weights["preferences"] = scale_weight_to_weeks(weights["preferences"], time_set["weeks"])

    # Scale weights relatively
    weights = scale_weights_relatively(weights, staff)

    # Scale weights to hours
    weights["excess demand deviation factor"] = scale_weight_to_hours(
        weights["excess demand deviation factor"], time_set["step"]
    )
    weights["deficit demand deviation factor"] = scale_weight_to_hours(
        weights["deficit demand deviation factor"], time_set["step"]
    )
    weights["preferences"] = scale_weight_to_hours(weights["preferences"], time_set["step"])

    # Scale up weights
    weights = scale_up_weights(weights, staff["employees"])

    return weights


def scale_weight_to_hours(weight, time_step):
    """
    Demand deviation and preferences needs to be scaled to hours, as this is the
    reference time step.
    """

    weight *= time_step

    return weight


def scale_weight_to_weeks(weight, weeks):

    weight *= len(weeks)

    return weight


def scale_weights_relatively(weights, staff):

    num_employees = len(staff["employees"])
    employee_contracted_hours = staff["employee_contracted_hours"]

    weights = scale_contracted_hours_relatively(weights, employee_contracted_hours)

    weights["lowest fairness score"] = scale_based_on_staff_sized(
        weights["lowest fairness score"], num_employees
    )

    return weights


def scale_contracted_hours_relatively(weights, employee_contracted_hours):
    """
    Contracted hours weight is scaled for each employee based on the ratio between contracted hours
    and default contracted hours. Scaling factor allows for
    """

    contracted_hours_weights = tupledict()
    scaling_factor = 1.0

    for e in employee_contracted_hours:
        contracted_hours_weights[e] = (
            scaling_factor
            * weights["contracted hours"]
            * (DEFAULT_CONTRACTED_HOURS / employee_contracted_hours[e])
        )

    weights["contracted hours"] = contracted_hours_weights

    return weights


def scale_based_on_staff_sized(weight, num_employees):
    """ Scale weight relatively to number of employees """

    weight *= num_employees

    return weight


def scale_up_weights(weights, employees):

    scaling_factor = 1

    weights["excess demand deviation factor"] *= scaling_factor
    weights["deficit demand deviation factor"] *= scaling_factor
    weights["rest"] *= scaling_factor
    weights["partial weekends"] *= scaling_factor
    weights["isolated working days"] *= scaling_factor
    weights["isolated off days"] *= scaling_factor
    weights["consecutive days"] *= scaling_factor
    weights["preferences"] *= scaling_factor

    for e in employees:
        weights["contracted hours"][e] *= scaling_factor

    return weights
