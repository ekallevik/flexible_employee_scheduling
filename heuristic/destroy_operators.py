from heuristic.delta_calculations import calc_weekly_objective_function
from heuristic.converter import set_x

def worst_week_removal(state, competencies, time_periods_in_week, employees, weeks, L_C_D, shifts_in_week, t_covered_by_shift):
    k = 1
    value = calc_weekly_objective_function(state, competencies, time_periods_in_week, employees, weeks, L_C_D, k)
    for j in value:
        destroy_set_shifts = [set_x(state, t_covered_by_shift, e, t, v, 0) for e in employees for t,v in shifts_in_week[j] if state.x[e,t,v] == 1]
        for e in employees:
            state.w[e,j] =(0, 0.0)
    return destroy_set_shifts, value

def worst_employee_removal(state, destroy_size, shifts, t_covered_by_shift):
    f_sorted = sorted(state.f, key=state.f.get, reverse=True)
    employees = []
    employees.extend(f_sorted[:destroy_size])
    employees.extend(f_sorted[-destroy_size:])
    
    destroy_set = [set_x(state, t_covered_by_shift, e, t, v, 0) for e in employees for t,v in shifts if state.x[e,t,v] != 0]

    return destroy_set, employees