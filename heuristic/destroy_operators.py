from heuristic.delta_calculations import calc_weekly_objective_function
from heuristic.converter import set_x

def worst_week_removal(competencies, time_periods_in_week, combined_time_periods_in_week, employees, weeks, L_C_D, shifts_in_week, t_covered_by_shift, state, destroy_size=1):
    #print("worst_week_removal is running")
    worst_k_weeks = calc_weekly_objective_function(state, competencies, time_periods_in_week, combined_time_periods_in_week, employees, weeks, L_C_D, destroy_size, "worst")
    destroy_set_shifts = [set_x(state, t_covered_by_shift, e, t, v, 0) for j in worst_k_weeks for e in employees for t,v in shifts_in_week[j] if state.x[e,t,v] == 1]
    return destroy_set_shifts, worst_k_weeks

def worst_employee_removal(shifts, t_covered_by_shift, state, destroy_size=2):
    #print("worst_employee_removal is running")
    f_sorted = sorted(state.f, key=state.f.get, reverse=True)
    employees = []
    employees.extend(f_sorted[:destroy_size] + f_sorted[-destroy_size:])
    destroy_set = [set_x(state, t_covered_by_shift, e, t, v, 0) for e in employees for t,v in shifts if state.x[e,t,v] != 0]
    return destroy_set, employees
