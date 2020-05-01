from collections import defaultdict
from copy import copy
from operator import itemgetter


def calculate_deviation_from_demand(
    state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_repair_set
):
    for c in competencies:
        for e2, t, v in destroy_repair_set:
            for t in t_covered_by_shift[t, v]:
                state.soft_vars["deviation_from_ideal_demand"][c, t] = (
                    sum(state.y[c, e, t] for e in employee_with_competencies[c])
                    - demand["ideal"][c, t]
                )


def delta_calculate_negative_deviation_from_contracted_hours(
    state, employees, contracted_hours, weeks, time_periods_in_week, competencies, time_step
):
    """
    Calculates both negative and positive contracted hours (The name should be updated but haven't had time yet)
    It checks the employees where a change has been made whether destroyed or repaired. 
    Then calculates the deviation only for these employees
    
    I have decided to also include checking the hard constraint if we are above contracted hours in this function as well
    This is done as it is easy to do at the same time and saveds time.
    Another update comes in another PR that updates the soft variables of contracted hours to weekly contracted hours
    """
    for e in employees:
        for j in weeks:
            state.soft_vars["contracted_hours"][
                e, j
            ] = deviation_contracted_hours = contracted_hours[e] - sum(
                time_step * state.y[c, e, t] for t in time_periods_in_week[j] for c in competencies
            )

        state.hard_vars["delta_positive_contracted_hours"][e] = -min(
            0, sum(state.soft_vars["contracted_hours"][e, j] for j in weeks)
        )

    # for e,t,v in destroy_set:
    #     state.soft_vars["contracted_hours"][e] += v

    # for e,t,v in repair_set:
    #     state.soft_vars["contracted_hours"][e] -= v


def calculate_weekly_rest(state, shifts_at_week, employees, weeks):
    """
        A function that calculates the longest possible weekly rest an employe can have
        based on the shifts that employee is assigned. 

        If no weekly rest is possible (meaning no rest period is longer than the required number of hours)
        the hard constraint is broken and the hard variable corresponding to weekly rest gets a
        value of 1 for the week the constraint is broken. 

    """
    weeks = copy(weeks)
    actual_shifts = {
        (e, j): [(t, v) for t, v in shifts_at_week[j] if state.x[e, t, v] == 1]
        for e in employees
        for j in weeks
    }
    off_shift_periods = defaultdict(list)
    weeks.append(weeks[-1] + 1)
    important = [7 * 24 * i for i in weeks]
    for key in actual_shifts.keys():
        week = int(weeks.index(key[1]))
        if len(actual_shifts[key]) == 0:
            off_shift_periods[key] = [
                (important[week], float((important[week + 1] - important[week])))
            ]

        else:
            if actual_shifts[key][0][0] - important[week] >= 36:
                off_shift_periods[key].append(
                    (important[week], actual_shifts[key][0][0] - important[week])
                )

            if important[week + 1] - (actual_shifts[key][-1][0] + actual_shifts[key][-1][1]) >= 36:
                off_shift_periods[key].append(
                    (
                        (actual_shifts[key][-1][0] + actual_shifts[key][-1][1]),
                        important[week + 1]
                        - (actual_shifts[key][-1][0] + actual_shifts[key][-1][1]),
                    )
                )

            for i in range(len(actual_shifts[key]) - 1):
                if (
                    actual_shifts[key][i + 1][0]
                    - (actual_shifts[key][i][0] + actual_shifts[key][i][1])
                    >= 36
                ):
                    off_shift_periods[key].append(
                        (
                            (actual_shifts[key][i][0] + actual_shifts[key][i][1]),
                            actual_shifts[key][i + 1][0]
                            - (actual_shifts[key][i][0] + actual_shifts[key][i][1]),
                        )
                    )

        if len(off_shift_periods[key]) != 0:
            state.w[key] = max(off_shift_periods[key], key=itemgetter(1))
            state.hard_vars["weekly_off_shift_error"][key] = 0
        else:
            state.hard_vars["weekly_off_shift_error"][key] = 1
            state.w[key] = (0, 0.0)


# Weaknesses:
# 1. It checks every weekend instead of only the weekends that have been destroyed or repaired
def calculate_partial_weekends(state, employees, shifts_at_day, saturdays):
    for e in employees:
        for i in saturdays:
            state.soft_vars["partial_weekends"][e, i] = abs(
                sum(state.x[e, t, v] for t, v in shifts_at_day[i])
                - sum(state.x[e, t, v] for t, v in shifts_at_day[i + 1])
            )


# Weaknesses:
# 1. It checks every possible combination of isolated working days instead of the ones that could be affected by the destroy and repair
def calculate_isolated_working_days(state, employees, shifts_at_day, days):
    for e in employees:
        for i in range(len(days) - 2):
            state.soft_vars["isolated_working_days"][e, i + 1] = max(
                0,
                (
                    -sum(state.x[e, t, v] for t, v in shifts_at_day[i])
                    + sum(state.x[e, t, v] for t, v in shifts_at_day[i + 1])
                    - sum(state.x[e, t, v] for t, v in shifts_at_day[i + 2])
                ),
            )


# Weaknesses:
# 1. It checks every possible combination of isolated off days instead of the ones that could be affected by the destroy and repair
def calculate_isolated_off_days(state, employees, shifts_at_day, days):
    for e in employees:
        for i in range(len(days) - 2):
            state.soft_vars["isolated_off_days"][e, i + 1] = max(
                0,
                (
                    sum(state.x[e, t, v] for t, v in shifts_at_day[i])
                    - sum(state.x[e, t, v] for t, v in shifts_at_day[i + 1])
                    + sum(state.x[e, t, v] for t, v in shifts_at_day[i + 2])
                    - 1
                ),
            )


# Weaknesses:
# 1. It checks every possible combination of consecutive days instead of the ones that could be affected by the destroy and repair
def calculate_consecutive_days(state, employees, shifts_at_day, L_C_D, days):
    for e in employees:
        for i in range(len(days) - L_C_D):
            state.soft_vars["consecutive_days"][e, i] = max(
                0,
                (
                    sum(
                        sum(state.x[e, t, v] for t, v in shifts_at_day[i_marked])
                        for i_marked in range(i, i + L_C_D)
                    )
                )
                - L_C_D,
            )


def calculate_f(state, employees, off_shifts, saturdays, days, L_C_D, weeks):
    for e in employees:
        state.f[e] = (
            sum(state.w[e, j][1] - state.soft_vars["contracted_hours"][e, j] for j in weeks)
            - sum(state.soft_vars["partial_weekends"][e, i] for i in saturdays)
            - sum(
                state.soft_vars["isolated_working_days"][e, i + 1]
                + state.soft_vars["isolated_off_days"][e, i + 1]
                for i in range(len(days) - 2)
            )
            - sum(state.soft_vars["consecutive_days"][e, i] for i in range(len(days) - L_C_D))
        )


def below_minimum_demand(
    state, repair_destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift
):
    for c in competencies:
        for e2, t1, v1 in repair_destroy_set:
            for t in t_covered_by_shift[t1, v1]:
                state.hard_vars["below_minimum_demand"][c, t] = max(
                    0,
                    (
                        demand["min"][c, t]
                        - sum(state.y[c, e, t] for e in employee_with_competencies[c])
                    ),
                )


def above_maximum_demand(
    state, repair_destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift
):
    for c in competencies:
        for e2, t1, v1 in repair_destroy_set:
            for t in t_covered_by_shift[t1, v1]:
                state.hard_vars["above_maximum_demand"][c, t] = max(
                    0,
                    (
                        sum(state.y[c, e, t] for e in employee_with_competencies[c])
                        - demand["max"][c, t]
                    ),
                )


def more_than_one_shift_per_day(state, employees, demand, shifts_at_day, days):
    for e in employees:
        for i in days:
            state.hard_vars["more_than_one_shift_per_day"][e, i] = max(
                0, (sum(state.x[e, t, v] for t, v in shifts_at_day[i]) - 1)
            )


def cover_multiple_demand_periods(state, repair_set, t_covered_by_shift, competencies):
    for e, t1, v1 in repair_set:
        for t in t_covered_by_shift[t1, v1]:
            state.hard_vars["cover_multiple_demand_periods"][e, t] = max(
                0, (sum(state.y[c, e, t] for c in competencies) - 1)
            )


# I think this is not needed, but I am not sure yet
# def weekly_off_shift_error(state, repair_destroy_set, weeks, off_shift_in_week):
#   for e,t,v in repair_destroy_set:
#      for j in weeks:
#         state.hard_vars["weekly_off_shift_error"][e,j] = max(0,(abs(sum(state.w[e,t,v] for t,v in off_shift_in_week[j]) - 1)))

# This check might also not be needed as our off-shifts are based on time between shifts. As with the constraint above I am not sure
# def no_work_during_off_shift(state, repair_destroy_set, competencies, t_covered_by_off_shift, off_shifts):
#     for e,t2,v2 in repair_destroy_set:
#         for t1,v1 in off_shifts:
#             if state.w[e,t1,v1] != 0:
#                 state.hard_vars["no_work_during_off_shift"][e,t1] = sum(state.y[c,e,t] for c in competencies for t in t_covered_by_off_shift[t1,v1])

# This check might not be needed if we always set y's when we set x.
def mapping_shift_to_demand(
    state, repair_destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies
):
    for e, t1, v1 in repair_destroy_set:
        for t in t_covered_by_shift[t1, v1]:
            state.hard_vars["mapping_shift_to_demand"][e, t] = max(
                0,
                abs(
                    sum(state.x[e, t_marked, v] for t_marked, v in shifts_overlapping_t[t])
                    - sum(state.y[c, e, t] for c in competencies)
                ),
            )


# def calculate_positive_deviation_from_contracted_hours(state, destroy_set, repair_set):
#     for e,t,v in destroy_set:
#         state.hard_vars["delta_positive_contracted_hours"][e] -= v

#     for e,t,v in repair_set:
#         state.hard_vars["delta_positive_contracted_hours"][e] += v


def hard_constraint_penalties(state):
    below_demand = sum(state.hard_vars["below_minimum_demand"].values())
    above_demand = sum(state.hard_vars["above_maximum_demand"].values())
    break_one_shift_per_day = sum(state.hard_vars["more_than_one_shift_per_day"].values())
    break_one_demand_per_time = sum(state.hard_vars["cover_multiple_demand_periods"].values())
    break_weekly_off = sum(state.hard_vars["weekly_off_shift_error"].values())
    # break_no_work_during_off_shift = sum(state.hard_vars["no_work_during_off_shift"].values())
    break_shift_to_demand = sum(state.hard_vars["mapping_shift_to_demand"].values())
    break_contracted_hours = sum(state.hard_vars["delta_positive_contracted_hours"].values())

    hard_penalties = (
        below_demand
        + above_demand
        + break_one_shift_per_day
        + break_one_demand_per_time
        + break_weekly_off
        + break_shift_to_demand
        + break_contracted_hours
    )
    return hard_penalties


def calculate_objective_function(
    state, employees, off_shifts, saturdays, L_C_D, days, competencies, weeks
):
    calculate_f(state, employees, off_shifts, saturdays, days, L_C_D, weeks)
    g = min(state.f.values())
    state.objective_function_value = (
        sum(state.f.values())
        + g
        - abs(sum(state.soft_vars["deviation_from_ideal_demand"].values()))
        - 10 * hard_constraint_penalties(state)
    )


def calc_weekly_objective_function(
    state, competencies, time_periods_in_week, employees, weeks, L_C_D, k=1, setting="best"
):
    value = {}
    for j in weeks:
        days_in_week = [i for i in range(j * 7, (j + 1) * 7)]
        if setting == "worst":
            value[j] = (
                sum(state.w[e, j][1] for e in employees)
                - sum(
                    abs(state.soft_vars["deviation_from_ideal_demand"][c, t])
                    for c in competencies
                    for t in time_periods_in_week[j]
                )
                - sum(state.soft_vars["partial_weekends"][e, (5 + j * 7)] for e in employees)
                - sum(
                    state.soft_vars["isolated_working_days"][e, i + 1]
                    + state.soft_vars["isolated_off_days"][e, i + 1]
                    for e in employees
                    for i in range(len(days_in_week) - 2)
                )
                - sum(
                    state.soft_vars["consecutive_days"][e, i]
                    for e in employees
                    for i in range(len(days_in_week) - L_C_D)
                )
                - sum(
                    state.hard_vars["below_minimum_demand"][c, t]
                    + state.hard_vars["above_maximum_demand"][c, t]
                    for c in competencies
                    for j in weeks
                    for t in time_periods_in_week[j]
                )
                - sum(
                    state.hard_vars["more_than_one_shift_per_day"][e, i]
                    for e in employees
                    for i in days_in_week
                )
                - sum(
                    state.hard_vars["cover_multiple_demand_periods"][e, t]
                    for e in employees
                    for j in weeks
                    for t in time_periods_in_week[j]
                )
                - max(0, sum(state.soft_vars["contracted_hours"][e, j] for e in employees))
                - 100
                * sum(state.hard_vars["delta_positive_contracted_hours"][e] for e in employees)
            )
        else:
            value[j] = (
                +sum(min(100, state.w[e, j][1]) for e in employees)
                - sum(
                    abs(state.soft_vars["deviation_from_ideal_demand"][c, t])
                    for c in competencies
                    for t in time_periods_in_week[j]
                )
                - sum(state.soft_vars["partial_weekends"][e, (5 + j * 7)] for e in employees)
                - sum(
                    state.soft_vars["isolated_working_days"][e, i + 1]
                    + state.soft_vars["isolated_off_days"][e, i + 1]
                    for e in employees
                    for i in range(len(days_in_week) - 2)
                )
                - sum(
                    state.soft_vars["consecutive_days"][e, i]
                    for e in employees
                    for i in range(len(days_in_week) - L_C_D)
                )
                - sum(
                    state.hard_vars["below_minimum_demand"][c, t]
                    + state.hard_vars["above_maximum_demand"][c, t]
                    for c in competencies
                    for j in weeks
                    for t in time_periods_in_week[j]
                )
                - 10
                * sum(
                    state.hard_vars["more_than_one_shift_per_day"][e, i]
                    for e in employees
                    for i in days_in_week
                )
                - 10
                * sum(
                    state.hard_vars["cover_multiple_demand_periods"][e, t]
                    for e in employees
                    for j in weeks
                    for t in time_periods_in_week[j]
                )
                - 10 * max(0, sum(state.soft_vars["contracted_hours"][e, j] for e in employees))
                - 10 * sum(state.hard_vars["weekly_off_shift_error"][e, j] for e in employees)
                - 100
                * sum(state.hard_vars["delta_positive_contracted_hours"][e] for e in employees)
            )
    if setting == "worst":
        value = sorted(value, key=value.get, reverse=False)[:k]
        return value
    else:
        return list(value.values())


def regret_objective_function(
    state,
    employee,
    off_shifts,
    saturdays,
    days,
    L_C_D,
    weeks,
    contracted_hours,
    competencies,
    t_changed,
):

    return (
        +sum(min(100, state.w[employee, j][1]) for j in weeks)
        + max(0, sum(state.soft_vars["contracted_hours"][employee, j] for j in weeks))
        - sum(state.soft_vars["partial_weekends"][employee, i] for i in saturdays)
        - sum(
            state.soft_vars["isolated_working_days"][employee, i + 1]
            + state.soft_vars["isolated_off_days"][employee, i + 1]
            for i in range(len(days) - 2)
        )
        - sum(state.soft_vars["consecutive_days"][employee, i] for i in range(len(days) - L_C_D))
        - 10
        * sum(
            state.hard_vars["below_minimum_demand"][c, t] for c in competencies for t in t_changed
        )
        - 10
        * sum(
            state.hard_vars["above_maximum_demand"][c, t] for c in competencies for t in t_changed
        )
        - 10 * sum(state.hard_vars["more_than_one_shift_per_day"][employee, i] for i in days)
        - 10 * sum(state.hard_vars["cover_multiple_demand_periods"][employee, t] for t in t_changed)
        - 10 * sum(state.hard_vars["weekly_off_shift_error"][employee, j] for j in weeks)
        - 10 * sum(state.hard_vars["mapping_shift_to_demand"][employee, t] for t in t_changed)
        - 10 * state.hard_vars["delta_positive_contracted_hours"][employee]
    )
