from operator import itemgetter
from pprint import pprint

from loguru import logger

from heuristic.delta_calculations import calc_weekly_objective_function
from heuristic.converter import remove_x


def worst_week_removal(competencies, time_periods_in_week, combined_time_periods_in_week, employees, weeks, L_C_D, shifts_in_week, t_covered_by_shift_combined, state, destroy_size=1):

    worst_k_weeks = calc_weekly_objective_function(state, competencies, time_periods_in_week,
                                                   combined_time_periods_in_week, employees,
                                                   weeks,  L_C_D, destroy_size, "worst")

    destroy_set_shifts = destroy_shifts(competencies, employees, shifts_in_week, state,
                                        t_covered_by_shift_combined, worst_k_weeks)

    logger.info(f"Destroyed {destroy_size} worst weeks: {worst_k_weeks}")

    return destroy_set_shifts, worst_k_weeks


def weighted_random_week_removal(competencies, time_periods_in_week,
                                 combined_time_periods_in_week, employees, weeks, L_C_D,
                                 shifts_in_week, t_covered_by_shift, random_state, state,
                                 destroy_size=1):

    weekly_objective = calc_weekly_objective_function(state, competencies, time_periods_in_week,
                                                      combined_time_periods_in_week, employees,
                                                      weeks, L_C_D, destroy_size,
                                                      setting="best")

    probabilities = get_weighted_probabilities(weekly_objective)

    selected_weeks = list(random_state.choice(weeks, size=destroy_size, p=probabilities,
                                              replace=False))

    destroy_set_shifts = destroy_shifts(
        competencies, employees, shifts_in_week, state, t_covered_by_shift, selected_weeks
    )

    logger.info(f"Destroyed {destroy_size} selected weeks: {selected_weeks}")

    return destroy_set_shifts, selected_weeks


def random_week_removal(competencies, employees, weeks, shifts_in_week, t_covered_by_shift,
                        random_state, state,  destroy_size=1):

    selected_weeks = list(random_state.choice(weeks, size=destroy_size, replace=False))

    destroy_set_shifts = destroy_shifts(
        competencies, employees, shifts_in_week, state, t_covered_by_shift, selected_weeks
    )

    logger.info(f"Destroyed {destroy_size} random weeks: {selected_weeks}")

    return destroy_set_shifts, selected_weeks


def random_weekend_removal(
    competencies, employees, weeks, shifts_at_day, t_covered_by_shift, random_state, state,
        destroy_size=2,
):

    selected_weeks = list(random_state.choice(weeks, size=destroy_size, replace=False))

    shifts_in_weekend = []

    for week in selected_weeks:
        shifts_in_weekend.append(shifts_at_day[5 + week * 7])
        shifts_in_weekend.append(shifts_at_day[6 + week * 7])

    destroy_set_shifts = destroy_shifts(
        competencies, employees, shifts_at_day, state, t_covered_by_shift, selected_weeks
    )

    logger.info(f"Destroyed {destroy_size} random weekends: {selected_weeks}")

    return destroy_set_shifts, selected_weeks


def worst_employee_removal(shifts, t_covered_by_shift_combined, competencies, state, destroy_size=2):

    f_sorted = sorted(state.f, key=state.f.get, reverse=True)

    employees = []
    employees.extend(f_sorted[:destroy_size] + f_sorted[-destroy_size:])

    destroy_set = destroy_employees(
        competencies, employees, shifts, state, t_covered_by_shift_combined
    )

    logger.info(f"Destroyed {destroy_size} worst employees: {employees}")

    return destroy_set, employees

def worst_contract_removal(shifts, t_covered_by_shift_combined, competencies, weeks, employees,
                           state,
                           destroy_size=4):

    if destroy_size % 2 == 1:
        raise ValueError("The destroy size should be even")


    # todo: only use some weeks?

    worked_hours = {e: sum(state.soft_vars["deviation_contracted_hours"][e, j]
                           for j in weeks)
                    for e in employees}

    #breakpoint()

    selected_employees = []

    for _ in range(int(destroy_size / 2)):
        # TODO: does this have to by symmetric? Maybe have a balanced deficiency

        overworked_employee = max(worked_hours.items(), key=itemgetter(1))[0]

        logger.trace(f"Overworked employee {overworked_employee} chosen "
                     f"(v:{worked_hours[overworked_employee]})")

        selected_employees.append(overworked_employee)
        del worked_hours[overworked_employee]

        underworked_employee = min(worked_hours.items(), key=itemgetter(1))[0]

        logger.trace(f"Underworked employee {underworked_employee} chosen "
                     f"(v:{worked_hours[underworked_employee]})")

        selected_employees.append(underworked_employee)
        del worked_hours[underworked_employee]

    destroy_set = destroy_employees(
        competencies, selected_employees, shifts, state, t_covered_by_shift_combined
    )

    logger.error(f"Destroyed {destroy_size} worst employees: {selected_employees}")

    return destroy_set, selected_employees


def weighted_random_employee_removal(
    shifts, t_covered_by_shift, competencies, employees, random_state, state, destroy_size=2
):

    probabilities = get_weighted_probabilities(state.f)

    selected_employees = list(random_state.choice(employees, size=destroy_size, p=probabilities,
                                                  replace=False))

    destroy_set = destroy_employees(
        competencies, selected_employees, shifts, state, t_covered_by_shift
    )

    logger.info(f"Destroyed {destroy_size} selected employees: {selected_employees}")

    return destroy_set, selected_employees


def random_employee_removal(
    shifts, t_covered_by_shift, competencies, employees, random_state, state, destroy_size=2
):

    selected_employees = random_state.choice(employees, size=destroy_size, replace=False)

    destroy_set = destroy_employees(
        competencies, selected_employees, shifts, state, t_covered_by_shift
    )

    logger.info(f"Destroyed {destroy_size} random employees: : {selected_employees}")

    logger.info(f"Destroyed {destroy_size} random employees")

    return destroy_set, selected_employees


def destroy_shifts(competencies, employees, shifts_in_week, state, t_covered_by_shift_combined,
                   worst_k_weeks):

    destroy_set_shifts = [
        remove_x(state, t_covered_by_shift_combined, competencies, e, t, v)
        for j in worst_k_weeks
        for e in employees for t, v in shifts_in_week[j] if state.x[e, t, v] == 1]

    return destroy_set_shifts


def destroy_employees(competencies, employees, shifts, state, t_covered_by_shift_combined):

    destroy_set = [
        remove_x(state, t_covered_by_shift_combined, competencies, e, t, v)
        for e in employees
        for t, v in shifts if state.x[e, t, v] != 0]

    return destroy_set


def get_weighted_probabilities(score):
    """
    Ensure that all probabilities in [0, 1], with the highest probability for the lowest
    score
    """

    # Shift all values by the max score, and flip the sign
    upper_bound = max(max(score), 0)
    shifted_score = [-(value - upper_bound) for value in score]
    total_weight = sum(shifted_score)
    adjusted_score = [value / total_weight for value in shifted_score]

    return adjusted_score
