from collections import defaultdict
from operator import itemgetter


def calculate_deviation_from_demand(model, y):
    delta = {}
    for c in model.competencies:
        for t in model.time_periods[c]:
            delta[c, t] = (
                sum(y[c, e, t] for e in model.employee_with_competencies[c])
                - model.demand["ideal"][c, t]
            )
    return delta


def calculate_weekly_rest(model, x, w):
    actual_shifts = {
        (e, j): [(t, v) for t, v in model.shifts_at_week[j] if x[e, t, v] == 1]
        for e in model.employees
        for j in model.weeks
    }
    off_shift_periods = defaultdict(list)
    important = [7 * 24 * i for i in range(len(model.weeks) + 1)]
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


def calculate_negative_deviation_from_demand(model, y):
    delta = {}
    for c in model.competencies:
        for i in model.days:
            for t in model.time_periods_in_day[i]:
                delta[c, t] = max(
                    0,
                    model.demand["ideal"][c, t]
                    - sum(y[c, e, t] for e in model.employee_with_competencies[c]),
                )
    return delta


def calculate_negative_deviation_from_contracted_hours(model, y):
    delta_negative_contracted_hours = {}
    for e in model.employees:
        for j in model.weeks:
            delta_negative_contracted_hours[e, j] = model.contracted_hours[e] - sum(
                model.time_step * y[c, e, t]
                for c in model.competencies
                for t in model.time_periods_in_week[c, j]
            )
    return delta_negative_contracted_hours


def calculate_partial_weekends(model, x):
    partial_weekend = {}
    partial_weekend_shifts = []
    for i in model.saturdays:
        for e in model.employees:
            partial_weekend[e, i] = abs(
                (
                    sum(x[e, t, v] for t, v in model.shifts_at_day[i])
                    - sum(x[e, t, v] for t, v in model.shifts_at_day[i + 1])
                )
            )
    return partial_weekend


def calculate_isolated_working_days(model, x):
    isolated_working_days = {}
    for e in model.employees:
        for i in range(len(model.days) - 2):
            isolated_working_days[e, i + 1] = max(
                0,
                (
                    -sum(x[e, t, v] for t, v in model.shifts_at_day[i])
                    + sum(x[e, t, v] for t, v in model.shifts_at_day[i + 1])
                    - sum(x[e, t, v] for t, v in model.shifts_at_day[i + 2])
                ),
            )
    return isolated_working_days


def calculate_isolated_off_days(model, x):
    isolated_off_days = {}
    for e in model.employees:
        for i in range(len(model.days) - 2):
            isolated_off_days[e, i + 1] = max(
                0,
                (
                    sum(x[e, t, v] for t, v in model.shifts_at_day[i])
                    - sum(x[e, t, v] for t, v in model.shifts_at_day[i + 1])
                    + sum(x[e, t, v] for t, v in model.shifts_at_day[i + 2])
                    - 1
                ),
            )
    return isolated_off_days


def calculate_consecutive_days(model, x):
    consecutive_days = {}
    for e in model.employees:
        for i in range(len(model.days) - model.L_C_D):
            consecutive_days[e, i] = max(
                0,
                (
                    sum(
                        sum(x[e, t, v] for t, v in model.shifts_at_day[i_marked])
                        for i_marked in range(i, i + model.L_C_D)
                    )
                )
                - model.L_C_D,
            )
    return consecutive_days


def calculate_f(model, soft_vars, w, employees=None):
    if employees == None:
        employees = model.employees
    f = {}
    for e in employees:
        f[e] = (
            sum(w[e, j][1] for j in model.weeks)
            - sum(soft_vars["contracted_hours"][e, j] for j in model.weeks)
            - sum(soft_vars["partial_weekends"][e, i] for i in model.saturdays)
            - sum(
                soft_vars["isolated_working_days"][e, i + 1]
                + soft_vars["isolated_off_days"][e, i + 1]
                for i in range(len(model.days) - 2)
            )
            - sum(soft_vars["consecutive_days"][e, i] for i in range(len(model.days) - model.L_C_D))
        )
    return f


def calculate_objective_function(model, soft_vars, w):
    f = calculate_f(model, soft_vars, w)
    g = min(f.values())
    objective_function_value = (
        sum(f.values()) + g - abs(sum(soft_vars["deviation_from_ideal_demand"].values()))
    )
    return objective_function_value, f
