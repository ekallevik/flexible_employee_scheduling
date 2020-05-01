from collections import defaultdict
from operator import itemgetter

# todo: convert to class and store data to reduce overhead?


def calculate_deviation_from_demand(data, y):
    delta = {}

    employee_with_competencies = data["staff"]["employee_with_competencies"]

    for c in data["competencies"]:
        for t in data["time"]["periods"][0]:
            delta[c, t] = (
                    sum(y[c, e, t] for e in employee_with_competencies[c])
                    - data.demand["ideal"][c, t]
            )
    return delta


def calculate_weekly_rest(data, x, w):

    # todo: calculate and store this data earlier?
    actual_shifts = {
        (e, j): [(t, v) for t, v in data.shifts_at_week[j] if x[e, t, v] == 1]
        for e in data["staff"]["employees"]
        for j in data["time"]["weeks"]
    }

    off_shift_periods = defaultdict(list)
    important = [7 * 24 * i for i in range(len(data.weeks) + 1)]

    for key in actual_shifts.keys():
        week = int(key[1])
        if actual_shifts[key][0][0] - important[week] >= 36:
            off_shift_periods[key].append(
                (important[week], actual_shifts[key][0][0] - important[week])
            )

        if important[week + 1] - (actual_shifts[key][-1][0] + actual_shifts[key][-1][1]) >= 36:
            off_shift_periods[key].append(
                (
                    (actual_shifts[key][-1][0] + actual_shifts[key][-1][1]),
                    important[week + 1] - (actual_shifts[key][-1][0] + actual_shifts[key][-1][1]),
                )
            )

        for i in range(len(actual_shifts[key]) - 1):
            if (
                actual_shifts[key][i + 1][0] - (actual_shifts[key][i][0] + actual_shifts[key][i][1])
                >= 36
            ):
                off_shift_periods[key].append(
                    (
                        (actual_shifts[key][i][0] + actual_shifts[key][i][1]),
                        actual_shifts[key][i + 1][0]
                        - (actual_shifts[key][i][0] + actual_shifts[key][i][1]),
                    )
                )

    for key in off_shift_periods:
        w[key] = max(off_shift_periods[key], key=itemgetter(1))


def calculate_negative_deviation_from_demand(data, y):

    employees_with_competencies = data["staff"]["employees_with_competencies"]
    delta = {}

    for c in data["competencies"]:
        for i in data["time"]["days"]:
            # todo: increase the readability of this set
            for t in data["time"]["periods"][2][i]:
                delta[c, t] = max(
                    0,
                    data["demand"]["ideal"][c, t]
                    - sum(y[c, e, t] for e in employees_with_competencies[c]),
                )
    return delta


def calculate_negative_deviation_from_contracted_hours(data, y):

    time_periods_in_week = data["time"]["periods"][2]
    delta_negative_contracted_hours = {}

    for e in data["staff"]["employees"]:
        for j in data["time"]["weeks"]:
            delta_negative_contracted_hours[e, j] = data["staff"]["employee_contracted_hours"][e] - sum(
                data["time"]["step"] * y[c, e, t]
                for t in time_periods_in_week[j]
                for c in data["competencies"]
            )
    return delta_negative_contracted_hours


def calculate_partial_weekends(data, x):

    partial_weekend = {}

    for i in data["time"]["saturdays"]:
        for e in data["staff"]["employees"]:

            partial_weekend[e, i] = abs(
                sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i])
                - sum(x[e, t, v] for t, v in data["shifts"]["shifts_per_day"][i + 1])
            )
    return partial_weekend


def calculate_isolated_working_days(data, x):

    shifts_per_day = data["shifts"]["shifts_per_day"]
    isolated_working_days = {}

    for e in data["staff"]["employees"]:
        for i in range(len(data["time"]["days"]) - 2):
            isolated_working_days[e, i + 1] = max(
                0,
                (
                    -sum(x[e, t, v] for t, v in shifts_per_day[i])
                    + sum(x[e, t, v] for t, v in shifts_per_day[i + 1])
                    - sum(x[e, t, v] for t, v in shifts_per_day[i + 2])
                ),
            )
    return isolated_working_days


def calculate_isolated_off_days(data, x):

    shifts_per_day = data["shifts"]["shifts_per_day"]
    isolated_off_days = {}

    for e in data["staff"]["employees"]:
        for i in range(len(data["time"]["days"]) - 2):
            isolated_off_days[e, i + 1] = max(
                0,
                (
                    sum(x[e, t, v] for t, v in shifts_per_day[i])
                    - sum(x[e, t, v] for t, v in shifts_per_day[i + 1])
                    + sum(x[e, t, v] for t, v in shifts_per_day[i + 2])
                    - 1
                ),
            )
    return isolated_off_days


def calculate_consecutive_days(data, x):

    shifts_per_day = data["shifts"]["shifts_per_day"]
    consecutive_days = {}

    for e in data["staff"]["employees"]:
        for i in range(len(data["time"]["days"]) - data["limit_on_consecutive_days"]):

            consecutive_days[e, i] = max(
                0,
                (
                    sum(
                        sum(x[e, t, v] for t, v in shifts_per_day[i_marked])
                        for i_marked in range(i, i + data["limit_on_consecutive_days"])
                    )
                )
                - data["limit_on_consecutive_days"],
            )
    return consecutive_days


def calculate_f(data, soft_vars, w, employees=None):

    if not employees:
        employees = data["staff"]["employees"]

    f = {}

    # todo: add number_of_days to save calculations?
    days = data["time"]["days"]

    for e in employees:
        f[e] = (
            sum(w[e, j][1] for j in data["time"]["weeks"])
            - sum(soft_vars["deviation_contracted_hours"][e, j] for j in data["time"]["weeks"])
            - sum(soft_vars["partial_weekends"][e, i] for i in data["time"]["saturdays"])
            - sum(
                soft_vars["isolated_working_days"][e, i + 1]
                + soft_vars["isolated_off_days"][e, i + 1]
                for i in range(len(days) - 2)
            )
            - sum(soft_vars["consecutive_days"][e, i] for i in range(len(days) - data["limit_on_consecutive_days"]))
        )
    return f


def calculate_objective_function(model, soft_vars, w):

    f = calculate_f(model, soft_vars, w)
    g = min(f.values())

    # todo: temp solution while waiting on the correct key.
    try:
        objective_function_value = (
            sum(f.values()) + g - abs(sum(soft_vars["deviation_from_ideal_demand"].values()))
        )
    except Exception:
        objective_function_value = 0

    return objective_function_value, f

# todo: I am regarding all of the following as out of use. -Even
# Not needed at the moment and are not in use. Might be deleted at a later time when I know for sure.
def cover_minimum_demand(model, y):
    below_minimum_demand = {}
    for c in model.competencies:
        for t in model.time_periods:
            below_minimum_demand[c, t] = max(
                0,
                (
                    model.demand["min"][c, t]
                    - sum(y[c, e, t] for e in model.employees_with_competencies[c])
                ),
            )
    return below_minimum_demand


def under_maximum_demand(model, y):
    above_maximum_demand = {}
    for c in model.competencies:
        for t in model.time_periods:
            above_maximum_demand[c, t] = max(
                0,
                (
                    sum(y[c, e, t] for e in model.employee_with_competencies[c])
                    - model.demand["max"][c, t]
                ),
            )
    return above_maximum_demand


def maximum_one_shift_per_day(model, x):
    more_than_one_shift_per_day = {}
    for e in model.employees:
        for i in model.days:
            more_than_one_shift_per_day[e, i] = max(
                0, (sum(x[e, t, v] for t, v in model.shifts_at_day[i]) - 1)
            )
    return more_than_one_shift_per_day


def cover_only_one_demand_per_time_period(model, y):
    cover_multiple_demand_periods = {}
    for e in model.employees:
        for t in model.time_periods:
            cover_multiple_demand_periods[e, t] = max(
                0, (sum(y[c, e, t] for c in model.competencies) - 1)
            )
    return cover_multiple_demand_periods


def one_weekly_off_shift(model, w):
    weekly_off_shift_error = {}
    for e in model.employees:
        for j in model.weeks:
            weekly_off_shift_error[e, j] = max(
                0, (abs(sum(w[e, t, v] for t, v in model.off_shift_in_week[j]) - 1))
            )
    return weekly_off_shift_error


# Version 2
def no_work_during_off_shift2(model, w, y):
    no_work_during_off_shift = {}
    for e, t1, v1 in model.w:
        if w[e, t1, v1] == 1:
            no_work_during_off_shift[e, t1] = sum(
                y[c, e, t] for c in model.competencies for t in model.t_in_off_shifts[t1, v1]
            )
    return no_work_during_off_shift


# Version 1
def no_work_during_off_shift1(model, w, x):
    no_work_during_off_shift = {}
    for e in model.employees:
        for t, v in model.off_shifts:
            no_work_during_off_shift[e, t, v] = max(
                0,
                (len(model.shifts_covered_by_off_shift[t, v]) * w[e, t, v])
                - sum(
                    (1 - x[e, t_marked, v_marked])
                    for t_marked, v_marked in model.shifts_covered_by_off_shift[t, v]
                ),
            )
    return no_work_during_off_shift


def mapping_shift_to_demand(model, x, y):
    mapping_shift_to_demand = {}
    for e in model.employees:
        for t in model.time_periods:
            mapping_shift_to_demand[e, t] = max(
                0,
                abs(
                    sum(x[e, t_marked, v] for t_marked, v in model.shifts_overlapping_t[t])
                    - sum(y[c, e, t] for c in model.competencies)
                ),
            )
    return mapping_shift_to_demand


def calculate_positive_deviation_from_contracted_hours(model, y):
    delta_positive_contracted_hours = {}
    for e in model.employees:
        delta_positive_contracted_hours[e] = max(
            0,
            sum(
                model.time_step * y[c, e, t] for t in model.time_periods for c in model.competencies
            )
            - len(model.weeks) * model.contracted_hours[e],
        )
    return delta_positive_contracted_hours
