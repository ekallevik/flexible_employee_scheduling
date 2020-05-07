from heuristic.delta_calculations import calc_weekly_objective_function
from heuristic.converter import remove_x


def worst_week_removal(
    competencies,
    time_periods_in_week,
    employees,
    weeks,
    L_C_D,
    shifts_in_week,
    t_covered_by_shift,
    state,
    destroy_size=1,
):
    worst_k_weeks = calc_weekly_objective_function(
        state, competencies, time_periods_in_week, employees, weeks, L_C_D, destroy_size, "worst"
    )

    destroy_set_shifts = destroy_shifts(
        employees, shifts_in_week, state, t_covered_by_shift, worst_k_weeks
    )

    return destroy_set_shifts, worst_k_weeks


def random_week_removal(
    employees, weeks, shifts_in_week, t_covered_by_shift, state, random_state, destroy_size=1,
):

    selected_weeks = random_state.choice(weeks, size=destroy_size)

    destroy_set_shifts = destroy_shifts(
        employees, shifts_in_week, state, t_covered_by_shift, selected_weeks
    )

    return destroy_set_shifts, selected_weeks


def weighted_random_week_removal(
    competencies,
    time_periods_in_week,
    employees,
    weeks,
    L_C_D,
    shifts_in_week,
    t_covered_by_shift,
    state,
    random_state,
    destroy_size=1,
):

    weekly_objective = calc_weekly_objective_function(
        state,
        competencies,
        time_periods_in_week,
        employees,
        weeks,
        L_C_D,
        destroy_size,
        setting="best",
    )

    selected_weeks = random_state.choice(weeks, size=destroy_size, p=weekly_objective)

    destroy_set_shifts = destroy_shifts(
        employees, shifts_in_week, state, t_covered_by_shift, selected_weeks
    )

    return destroy_set_shifts, selected_weeks


def destroy_shifts(employees, shifts_in_week, state, t_covered_by_shift, worst_k_weeks):
    destroy_set_shifts = [
        set_x(state, t_covered_by_shift, e, t, v, 0)
        for j in worst_k_weeks
        for e in employees
        for t, v in shifts_in_week[j]
        if state.x[e, t, v] == 1
    ]
    return destroy_set_shifts


    destroy_set_shifts = [remove_x(state, t_covered_by_shift_combined, competencies, e, t, v) for j in worst_k_weeks for e in employees for t,v in shifts_in_week[j] if state.x[e,t,v] == 1]
    return destroy_set_shifts, worst_k_weeks

def worst_employee_removal(shifts, t_covered_by_shift_combined, competencies, state, destroy_size=2):
    f_sorted = sorted(state.f, key=state.f.get, reverse=True)
    employees = []
    employees.extend(f_sorted[:destroy_size] + f_sorted[-destroy_size:])

    destroy_set = destroy_employees(employees, shifts, state, t_covered_by_shift)

    return destroy_set, employees


def random_employee_removal(shifts, t_covered_by_shift, state, employees, random_state,
                            destroy_size=2):

    selected_employees = random_state.choice(employees, size=destroy_size)

    destroy_set = destroy_employees(selected_employees, shifts, state, t_covered_by_shift)

    return destroy_set, selected_employees


def weighted_random_employee_removal(
    shifts, t_covered_by_shift, state, employees, random_state, destroy_size=2
):

    selected_employees = random_state.choice(employees, size=destroy_size, p=state.f)

    destroy_set = destroy_employees(selected_employees, shifts, state, t_covered_by_shift)

    return destroy_set, selected_employees


def destroy_employees(employees, shifts, state, t_covered_by_shift):
    destroy_set = [
        set_x(state, t_covered_by_shift, e, t, v, 0)
        for e in employees
        for t, v in shifts
        if state.x[e, t, v] != 0
    ]
    return destroy_set
