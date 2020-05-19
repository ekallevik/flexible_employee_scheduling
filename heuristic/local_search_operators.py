from heuristic.delta_calculations import (
    calc_weekly_objective_function,
    calculate_consecutive_days,
    calculate_isolated_off_days,
    calculate_isolated_working_days,
    calculate_partial_weekends,
    calculate_weekly_rest,
    delta_calculate_negative_deviation_from_contracted_hours,
    employee_shift_value,
    worst_employee_regret_value
)
from heuristic.converter import set_x, remove_x
from operator import itemgetter
from random import choice
from utils.const import DESIRED_SHIFT_DURATION
import itertools

def illegal_week_swap(
    shifts_in_week,
    employees,
    shifts_at_day,
    t_covered_by_shift,
    competencies,
    contracted_hours,
    invalid_shifts, 
    shift_combinations_violating_daily_rest, 
    shift_sequences_violating_daily_rest,
    time_periods_in_week,
    time_step,
    L_C_D,
    weeks,
    combined_time_periods_in_week,
    state,
):
    destroy_set = []
    repair_set = []
    already_fixed_employees = []
    for emp, j in state.hard_vars["weekly_off_shift_error"]:
        if state.hard_vars["weekly_off_shift_error"][emp,j] == 1:
            shifts = [(t, v) for t, v in shifts_in_week[j] if state.x[emp,t,v] != 0]
            days_in_week = [i + (7 * j) for i in range(7)]
            saturdays = [5 + (j * 7)]
            sundays = [6 + (j * 7)]
            objective_values = {}
            for shift in shifts:
                current_state = state.copy()
                possible_employees = [e for e in employees if sum(current_state.x[e,t,v] for t,v in shifts_at_day[int(shift[0]/24)]) == 0 and (e,j) not in already_fixed_employees]

                set_x(current_state, t_covered_by_shift, emp, shift[0], shift[1], 0)

                calculate_weekly_rest(current_state, shifts_in_week, [emp], [j])
                calculate_partial_weekends(current_state, [emp], shifts_at_day, saturdays)
                calculate_isolated_working_days(current_state, [emp], shifts_at_day, days_in_week)
                calculate_isolated_off_days(current_state, [emp], shifts_at_day, days_in_week)
                calculate_consecutive_days(current_state, [emp], shifts_at_day, L_C_D, days_in_week)
                delta_calculate_negative_deviation_from_contracted_hours(current_state, [emp], contracted_hours, weeks, time_periods_in_week, competencies, time_step)

                
                #if sum(state.soft_vars["contracted_hours"][e,j] for j in weeks) - shift[1] >= 0
                if len(possible_employees) == 0:
                    print("Not enough employees")

                for e_p in possible_employees:
                    objective_values[e_p, shift] = employee_shift_value(state, e_p, shift, saturdays, sundays, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, shifts_in_week, weeks, shifts_at_day, j, 0)

            max_value = max(objective_values.items(), key=itemgetter(1))[1]
            employee = choice([key for key, value in objective_values.items() if value == max_value])

            already_fixed_employees.append((emp, j))

            repair_set.append(set_x(state, t_covered_by_shift, employee[0], employee[1][0], employee[1][1], 1))
            destroy_set.append(remove_x(state, t_covered_by_shift, competencies, emp, employee[1][0], employee[1][1]))

    return destroy_set, repair_set


def illegal_contracted_hours(state, shifts, time_step, employees, shifts_in_day, weeks, t_covered_by_shift, contracted_hours, time_periods_in_week, competencies):
    destroy_set = []
    repair_set = []
    delta_calculate_negative_deviation_from_contracted_hours(state, employees, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
    for e in state.hard_vars["delta_positive_contracted_hours"]:
        if state.hard_vars["delta_positive_contracted_hours"][e] > 0:
            illegal_hours = state.hard_vars["delta_positive_contracted_hours"][e]
            illegal_shifts = [(e,t,v) for t,v in shifts if state.x[e,t,v] == 1]
            for e,t,v in illegal_shifts:
                swap_shifts = [(e,t1,v1) for e in employees for t1,v1 in shifts_in_day[int(t/24)] if state.x[e,t1,v1] == 1 and v1 < v and sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) + (v1 - v) >= 0]
                if(len(swap_shifts) != 0):
                    zero_shifts = [(e_2, t_2, v_2) for e_2, t_2, v_2 in swap_shifts if (v - v_2) == illegal_hours]
                    shift = min(swap_shifts, key=itemgetter(1)) if len(zero_shifts) == 0 else choice(zero_shifts)
                    #shift = choice(swap_shifts)
                    destroy_set.append(remove_x(state, t_covered_by_shift, competencies, e, t, v))
                    destroy_set.append(remove_x(state, t_covered_by_shift, competencies, shift[0], shift[1], shift[2]))

                    repair_set.append(set_x(state, t_covered_by_shift, e, shift[1], shift[2], 1))
                    repair_set.append(set_x(state, t_covered_by_shift, shift[0], t, v, 1))
                    delta_calculate_negative_deviation_from_contracted_hours(state, employees, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
                    illegal_hours -= (v - shift[2])

                    if(illegal_hours <= 0):
                        break
    return destroy_set, repair_set


def exploit_contracted_hours(state, shifts, t_covered_by_shift, 
                            weeks, employees, competencies, saturdays, 
                            sundays, invalid_shifts, 
                            shift_combinations_violating_daily_rest, 
                            shift_sequences_violating_daily_rest, 
                            shifts_at_week, shifts_at_day, days, time_step):
    destroy_set = []
    repair_set = []
    below_demand_shifts = {shift: sum((time_step if state.soft_vars["deviation_from_ideal_demand"][c,t] < 0 else 0) for c in competencies for t in t_covered_by_shift[shift]) for shift in shifts}
    contracted_hours_below = {}
    contracted_hours_above = {}
    print(below_demand_shifts)
    for e in employees:
        value = sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks)
        if 0 < value < DESIRED_SHIFT_DURATION[0]:
            contracted_hours_below[e] = value
        else:
            contracted_hours_above[e] = value
    
    actual_shifts = {e: [(t,v) for t,v in shifts if state.x[e,t,v] == 1] for e in employees}
    shifts_to_choose_from = {e: {(t_1, v_1): [(t,v) for t, v in below_demand_shifts if set(t_covered_by_shift[t_1, v_1]).issubset(t_covered_by_shift[t, v]) and 0 < v - v_1 <= contracted_hours_below[e]] for t_1, v_1 in actual_shifts[e]} for e in contracted_hours_below}