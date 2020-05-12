from collections import defaultdict
from operator import itemgetter
from copy import copy

from loguru import logger


def calculate_deviation_from_demand(data, y):
    delta = {}
    for c in data["competencies"]:
        for t in data["time"]["periods"][0][c]:
            delta[c, t] = (
                sum(y[c, e, t] for e in data["staff"]["employees_with_competencies"][c])
                - data["demand"]["ideal"][c, t]
            )
    return delta


def calculate_weekly_rest(data, x, w):
    actual_shifts = {
        (e, j): [(t, v) for t, v in data["shifts"]["shifts_at_week"][j] if x[e, t, v] == 1]
        for e in data["staff"]["employees"]
        for j in data["time"]["weeks"]
    }
    off_shift_periods = defaultdict(list)
    important = [7 * 24 * i for i in range(len(data["time"]["weeks"]) + 1)]
    for key in actual_shifts.keys():
        week = int(key[1])
        if(len(actual_shifts[key]) == 0):
            off_shift_periods[key] = [(important[week], float((important[week + 1] - important[week])))]

        else:
            if(actual_shifts[key][0][0] - important[week] >= 36):
                off_shift_periods[key].append((important[week], actual_shifts[key][0][0] - important[week]))

            if(actual_shifts[key][0][0] - important[week] >= 36):
                off_shift_periods[key].append((important[week], actual_shifts[key][0][0] - important[week]))

def calculate_negative_deviation_from_demand(data, y):
    delta = {}
    for c in data["competencies"]:
        for i in data["time"]["days"]:
            for t in data["time"]["periods"][2][i]:
                delta[c, t] = max(
                    0,
                    data["demand"]["ideal"][c, t]
                    - sum(y[c, e, t] for e in data["staff"]["employee_with_competencies"][c]),
                )
    return delta


def calculate_negative_deviation_from_contracted_hours(data, y):
    delta_negative_contracted_hours = {}
    for e in data["staff"]["employees"]:
        for j in data["time"]["weeks"]:
            delta_negative_contracted_hours[e, j] = data["staff"]["employee_contracted_hours"][
                e
            ] - sum(
                data["time"]["step"] * y[c, e, t]
                for c in data["competencies"]
                for t in data["time"]["periods"][1][c, j]
            )
    return delta_negative_contracted_hours


def calculate_partial_weekends(data, x):
    partial_weekend = {}
    for i in data["time"]["saturdays"]:
        for e in data["staff"]["employees"]:
            partial_weekend[e, i] = abs(
                (
                    sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i])
                    - sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i + 1])
                )
            )
    return partial_weekend


def calculate_isolated_working_days(data, x):
    isolated_working_days = {}
    for e in data["staff"]["employees"]:
        for i in range(len(data["time"]["days"]) - 2):
            isolated_working_days[e, i + 1] = max(
                0,
                (
                    -sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i])
                    + sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i + 1])
                    - sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i + 2])
                ),
            )
    return isolated_working_days


def calculate_isolated_off_days(data, x):
    isolated_off_days = {}
    for e in data["staff"]["employees"]:
        for i in range(data["time"]["number_of_days"] - 2):
            isolated_off_days[e, i + 1] = max(
                0,
                (
                    sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i])
                    - sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i + 1])
                    + sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i + 2])
                    - 1
                ),
            )
    return isolated_off_days


def calculate_consecutive_days(data, x):
    consecutive_days = {}
    for e in data["staff"]["employees"]:
        for i in range(data["time"]["number_of_days"] - data["limit_on_consecutive_days"]):
            consecutive_days[e, i] = max(
                0,
                (
                    sum(
                        sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i_marked])
                        for i_marked in range(i, i + data["limit_on_consecutive_days"])
                    )
                )
                - data["limit_on_consecutive_days"],
            )
    return consecutive_days


def calculate_f(data, soft_vars, weights, w, employees=None):

    if not employees:
        employees = data["staff"]["employees"]

    f = {}
    for e in employees:
        f[e] = calculate_f_for_employee(data, e, soft_vars, weights, w)

    return f


def calculate_f_for_employee(data, e, soft_vars, weights, w):

    f = (
        weights["rest"] * sum(
            w[e, j][1]
            for j in data["time"]["weeks"]
        )

        - weights["contracted hours"][e] * sum(
            soft_vars["deviation_contracted_hours"][e, j]
            for j in data["time"]["weeks"]
        )


        - weights["partial weekends"] * sum(
            soft_vars["partial_weekends"][e, i]
            for i in data["time"]["saturdays"]
        )

        - sum(
            weights["isolated working days"] * soft_vars["isolated_working_days"][e, i + 1]
            + weights["isolated off days"] * soft_vars["isolated_off_days"][e, i + 1]
            for i in range(data["time"]["number_of_days"] - 2)
        )

        - weights["consecutive days"] * sum(
            soft_vars["consecutive_days"][e, i]
            for i in range(data["time"]["number_of_days"] - data["limit_on_consecutive_days"])
        )
    )

    return f


def calculate_objective_function(data, soft_vars, weights, w):

    f = calculate_f(data, soft_vars, weights, w)
    g = min(f.values())

    # todo: Split demand deviation into positive and negative

    objective_function_value = (
        sum(f.values())
        + g
        - weights["excess demand deviation factor"] * abs(sum(soft_vars["deviation_from_ideal_demand"].values()))
    )

    logger.info(f"Total-objective: {objective_function_value: .2f}")
    return objective_function_value, f
