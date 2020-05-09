from heuristic.delta_calculations import calc_weekly_objective_function
from heuristic.converter import remove_x

def worst_week_removal(competencies, time_periods_in_week, combined_time_periods_in_week, employees, weeks, L_C_D, shifts_in_week, t_covered_by_shift_combined, state, destroy_size=1):
    worst_k_weeks = calc_weekly_objective_function(state, competencies, time_periods_in_week, combined_time_periods_in_week, employees, weeks, L_C_D, destroy_size, "worst")
    destroy_set_shifts = [remove_x(state, t_covered_by_shift_combined, competencies, e, t, v) for j in worst_k_weeks for e in employees for t,v in shifts_in_week[j] if state.x[e,t,v] == 1]
    return destroy_set_shifts, worst_k_weeks

def worst_employee_removal(shifts, t_covered_by_shift_combined, competencies, state, destroy_size=2):
    f_sorted = sorted(state.f, key=state.f.get, reverse=True)
    employees = []
    employees.extend(f_sorted[:destroy_size] + f_sorted[-destroy_size:])
    destroy_set = [remove_x(state, t_covered_by_shift_combined, competencies, e, t, v) for e in employees for t,v in shifts if state.x[e,t,v] != 0]
    return destroy_set, employees
