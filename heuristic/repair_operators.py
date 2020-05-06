from operator import itemgetter
from random import choice

from loguru import logger

from converter import set_x
from heuristic.delta_calculations import (
    above_maximum_demand,
    below_minimum_demand,
    calc_weekly_objective_function,
    calculate_consecutive_days,
    calculate_deviation_from_demand,
    calculate_isolated_off_days,
    calculate_isolated_working_days,
    calculate_partial_weekends,
    calculate_weekly_rest,
    cover_multiple_demand_periods,
    delta_calculate_deviation_from_contracted_hours,
    mapping_shift_to_demand,
    more_than_one_shift_per_day,
    regret_objective_function,
)


def worst_week_repair(
        shifts_in_week,
        competencies,
        t_covered_by_shift,
        employee_with_competencies,
        demand,
        time_step,
        time_periods_in_week,
        employees,
        contracted_hours,
        weeks,
        shifts_at_day,
        state,
        destroy_set,
        week,
):
    """
    A greedy repair operator based on destroying the worst week.
    The last three arguments are passed from its corresponding destroy operator.

    It finds the shift with highest deviation from demand.
    This shift is then assigned to the employee with highest deviation from contracted hours
    as long as that employee does not work on the day of the shift we are assigning.

    It continues to do so until either the total negative deviation from demand is below a
    threshold (6) or we do not have any employees to assign to this shift as all employees are
    working this day
    """

    logger.info("Running worst_week_regret")
    repair_set = []
    employees_changed = employees
    changed = destroy_set

    while True:
        calculate_deviation_from_demand(
            state, competencies, t_covered_by_shift, employee_with_competencies, demand, changed
        )

        delta_calculate_deviation_from_contracted_hours(
            state, employees_changed, contracted_hours, weeks, time_periods_in_week,
            competencies, time_step,
        )

        deviation_from_demand = get_negative_deviation_from_demand(competencies, state,
                                                                   time_periods_in_week[week[0]])

        if deviation_from_demand < 6:
            return repair_set

        shifts = get_adjusted_shifts(shifts_in_week[week[0]], competencies, state,
                                     t_covered_by_shift)

        shift = max(shifts.items(), key=itemgetter(1))[0]

        deviation_contracted_hours = get_deviation_from_contracted_hours(employees, shift,
                                                                         shifts_at_day, state, week)

        if len(deviation_contracted_hours.keys()) == 0:
            return repair_set

        e = max(deviation_contracted_hours.items(), key=itemgetter(1))[0]
        repair_set.append(set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1))
        employees_changed = [e]
        changed = [(e, shift[0], shift[1])]


def worst_week_regret_repair(
        shifts_in_week,
        competencies,
        t_covered_by_shift,
        employee_with_competencies,
        demand,
        time_step,
        time_periods_in_week,
        employees,
        contracted_hours,
        weeks,
        shifts_at_day,
        L_C_D,
        shifts_overlapping_t,
        state,
        destroy_set,
        week,
):
    """
    The decision variables are set in the destroy operator. This only applies to the x and y
    variables as w now is a implicit variable that should be calculated.
    At the beginning of a repair operator the soft variables and hard penalizing variables have
    not  been updated to reflect the current changes to the decision variables

    To be able to calculate the deviation from demand (as this is how we choose a shift to assign)
    we would have to update the deviation from demand for the shifts (t_covered_by_shift) that have
    been destroyed. This is done efficiently in delta_calculate_deviation_from_demand. It only
    checks the destroyed shifts (and their t's) and only in a negative direction (covering to much
    demand would give 0 in deviation)

    If the total deviation from demand (for the week/s in question) are below a threshold (6) we are
     satisfied and would return the repair_set with shifts (e,t,v) set

    If not we take the shift with highest deviation from demand (in the weeks in question) to be
    assigned. We only search for an employee to assign to this shift based on if the employee are
    not working the day the shift is on.

    Which hard variables are important to calculate?:
        1.  Above/Below demand is done on a destroy_repair_set basis. This means we would have to
        calculate the above and below to get correct hard variables here if they were broken before
        the destroy fixes it.
        A good thing here is that if we do so with the destroy_set we fix the entire week.
        This means we have a fresh start with no broken constraints this week.
        2.  More than one shift per day is calculated on a employee basis. It checks every day on
        that employee. This would have to be done before as we need it in the calculation. We cannot
        do this on each employee as we loop through them. We do have the days we would check
        though. Would also not need to do a calculation on these hard constraints, but rather
        just  set them to 0. Most likely this is faster.
        3.  Cover multiple demand periods are also done on a destroy_repair_set basis. It would
        have to be run before.
        4.  Mapping shift to demand is also done on a destroy_repair_set basis. Would have to be
        run before to start fresh.
        5.  Positive contracted hours. This is run together with negative contracted hours. This
        is  done on a employee and week basis. By not running it before for all employees we
        would, not have updated the contracted hours after the destroy when calculating the new
        objective function. This would result in a wrong objective value.
        6.  Weekly rest. When a week have been destroyed everyone starts with a full week of rest if
        calculated. If not we would continue with the rest they had before. The smartest move would
        be to start fresh here as well.

    Which soft variables are important to calculate?:
        1. Partial weekend are only depending on the employee. It is calculated for every week no
        matter what as it is not based on destroy_repair_set
        2. The same is true for isolated working days, isolated off days and consecutive days

    """

    logger.info("Running worst_week_repair")
    repair_set = []

    employees_changed = employees

    saturdays = [5 + j * 7 for j in week]
    days = [i + (7 * j) for j in week for i in range(7)]

    while True:
        # Initial phase to recalculate soft and hard variables of the destroyed weeks
        # Calculates deviation from demand first to see if we are done and can return
        calculate_deviation_from_demand(
            state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set
        )

        deviation_from_demand = get_negative_deviation_from_demand(competencies, state, time_periods_in_week[week[0]])

        shifts = get_adjusted_shifts(shifts_in_week[week[0]], competencies, state, t_covered_by_shift)

        shift = max(shifts.items(), key=itemgetter(1))[0]

        possible_employees = get_possible_employees(employees, shift, shifts_at_day, state)

        if should_stop_regret_search(deviation_from_demand, possible_employees, shift,
                                     state, weeks):
            return repair_set

        update_hard_variables(competencies, days, demand, destroy_set, employee_with_competencies,
                              employees_changed, shifts_at_day, shifts_overlapping_t, state,
                              t_covered_by_shift)

        update_soft_variables(L_C_D, competencies, contracted_hours, days, employees_changed,
                              saturdays, shifts_at_day, shifts_in_week, state, time_periods_in_week,
                              time_step, weeks)

        # Now we have to decide on which employee should be assigned this shift.
        # Since we want to do this through regret we have to calculate the objective function of
        # the state with that shift assigned to each employee.
        #
        # We have two options here:
        # 1. We could copy the state we are working with. We would have to use deepcopy which takes
        # time and resources.
        # 2. We could set the x value and then remove it again after calculation.
        # Might take a lot of time and resources.

        # Copy method
        objective_values = {}
        for e in possible_employees:
            current_state = state.copy()
            repaired = [set_x(current_state, t_covered_by_shift, e, shift[0], shift[1], 1)]

            # Soft restriction calculations
            calculate_deviation_from_demand(
                current_state,
                competencies,
                t_covered_by_shift,
                employee_with_competencies,
                demand,
                repaired,
            )
            calculate_weekly_rest(current_state, shifts_in_week, [e], week)
            calculate_partial_weekends(current_state, [e], shifts_at_day, saturdays)
            calculate_isolated_working_days(current_state, [e], shifts_at_day, days)
            calculate_isolated_off_days(current_state, [e], shifts_at_day, days)
            calculate_consecutive_days(current_state, [e], shifts_at_day, L_C_D, days)
            delta_calculate_deviation_from_contracted_hours(
                current_state,
                [e],
                contracted_hours,
                weeks,
                time_periods_in_week,
                competencies,
                time_step,
            )

            # Hard constraint calculations
            mapping_shift_to_demand(
                state, repaired, t_covered_by_shift, shifts_overlapping_t, competencies
            )
            cover_multiple_demand_periods(state, repaired, t_covered_by_shift, competencies)
            more_than_one_shift_per_day(current_state, [e], demand, shifts_at_day, days)
            above_maximum_demand(
                current_state,
                repaired,
                employee_with_competencies,
                demand,
                competencies,
                t_covered_by_shift,
            )
            below_minimum_demand(
                current_state,
                repaired,
                employee_with_competencies,
                demand,
                competencies,
                t_covered_by_shift,
            )

            # Calculate the objective function when the employee e is assigned the shift
            objective_values[e] = calc_weekly_objective_function(
                current_state, competencies, time_periods_in_week, employees, week, L_C_D
            )[0]

        max_value = max(objective_values.items(), key=itemgetter(1))[1]
        employee = choice([key for key, value in objective_values.items() if value == max_value])

        repair_set.append(set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1))
        employees_changed = [employee]
        destroy_set = [(employee, shift[0], shift[1])]


def worst_employee_repair(
        competencies,
        t_covered_by_shift,
        employee_with_competencies,
        demand,
        contracted_hours,
        weeks,
        time_periods_in_week,
        time_step,
        all_shifts,
        shifts_at_day,
        state,
        destroy_set,
        employees,
):
    """
    A greedy repair operator based on destroying the worst employee.
    The last three arguments are passed from its corresponding destroy operator.

    It finds the shift with highest deviation from demand.
    This shift is then assigned to the employee with highest deviation from contracted hours
    as long as that employee does not work on the day of the shift we are assigning.
    The difference between this operator and the worst week is that we only look at the
    employees we have destroyed in the destroy operator

    It continues to do so until either the total negative deviation from demand is below a
    threshold (6) or we do not have any employees to assign to this shift as all employees
    are working this day
    """

    logger.info("Running worst_employee_repair")
    repair_set = []
    destroy_set = destroy_set
    employees_changed = employees

    while True:
        calculate_deviation_from_demand(
            state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set
        )

        shifts = get_adjusted_shifts(all_shifts, competencies, state, t_covered_by_shift)

        shift = max(shifts.items(), key=itemgetter(1))[0]

        deviation_from_demand = get_negative_deviation_from_demand(competencies, state, t_covered_by_shift[shift[0], shift[1]])

        if deviation_from_demand < 6:
            return repair_set

        delta_calculate_deviation_from_contracted_hours(
            state, employees_changed, contracted_hours, weeks, time_periods_in_week,
            competencies, time_step,
        )

        deviation_contracted_hours = get_deviation_from_contracted_hours(employees, shift,
                                                                         shifts_at_day, state,
                                                                         weeks)

        if len(deviation_contracted_hours.keys()) == 0:
            return repair_set
        e = max(deviation_contracted_hours.items(), key=itemgetter(1))[0]

        repair_set.append(set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1))
        employees_changed = [e]
        destroy_set = [(e, shift[0], shift[1])]


def worst_employee_regret_repair(
        competencies,
        t_covered_by_shift,
        employee_with_competencies,
        demand,
        all_shifts,
        off_shifts,
        saturdays,
        days,
        L_C_D,
        weeks,
        shifts_at_day,
        shifts_in_week,
        contracted_hours,
        time_periods_in_week,
        time_step,
        shifts_overlapping_t,
        state,
        destroy_set,
        employees_changed,
):
    logger.info("Running worst_employee_regret")
    repair_set = []
    destroy_set = destroy_set

    while True:
        calculate_deviation_from_demand(
            state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set
        )

        shifts = get_adjusted_shifts(all_shifts, competencies, state, t_covered_by_shift)

        shift = max(shifts.items(), key=itemgetter(1))[0]

        deviation_from_demand = get_negative_deviation_from_demand(competencies, state,
                                                                   t_covered_by_shift[shift[0], shift[1]])

        possible_employees = get_possible_employees(employees_changed, shift, shifts_at_day, state)

        if should_stop_regret_search(deviation_from_demand, possible_employees, shift,
                                     state, weeks):
            return repair_set

        # Initial phase to recalculate soft and hard variables of the destroyed weeks
        # Hard Restrictions/Variables
        update_hard_variables(competencies, days, demand, destroy_set, employee_with_competencies,
                              employees_changed, shifts_at_day, shifts_overlapping_t, state,
                              t_covered_by_shift)

        # Soft Restrictions/Variables
        update_soft_variables(L_C_D, competencies, contracted_hours, days, employees_changed,
                              saturdays, shifts_at_day, shifts_in_week, state, time_periods_in_week,
                              time_step, weeks)

        below_minimum_demand(
            state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift
        )
        above_maximum_demand(
            state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift
        )
        cover_multiple_demand_periods(state, destroy_set, t_covered_by_shift, competencies)
        mapping_shift_to_demand(
            state, destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies
        )

        employee_objective_functions = {}
        for e in possible_employees:
            repaired = [set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1)]

            # Calculations needed for soft constraints to be updated after repair
            delta_calculate_deviation_from_contracted_hours(
                state, [e], contracted_hours, weeks, time_periods_in_week, competencies, time_step
            )
            calculate_weekly_rest(state, shifts_in_week, [e], weeks)
            calculate_partial_weekends(state, [e], shifts_at_day, saturdays)
            calculate_isolated_working_days(state, [e], shifts_at_day, days)
            calculate_isolated_off_days(state, [e], shifts_at_day, days)
            calculate_consecutive_days(state, [e], shifts_at_day, L_C_D, days)

            # Hard restriction:
            below_minimum_demand(
                state,
                repaired,
                employee_with_competencies,
                demand,
                competencies,
                t_covered_by_shift,
            )
            above_maximum_demand(
                state,
                repaired,
                employee_with_competencies,
                demand,
                competencies,
                t_covered_by_shift,
            )
            more_than_one_shift_per_day(state, [e], demand, shifts_at_day, days)
            cover_multiple_demand_periods(state, repaired, t_covered_by_shift, competencies)
            mapping_shift_to_demand(
                state, repaired, t_covered_by_shift, shifts_overlapping_t, competencies
            )

            # Stores the objective function for this employee
            employee_objective_functions[e] = regret_objective_function(
                state,
                e,
                off_shifts,
                saturdays,
                days,
                L_C_D,
                weeks,
                contracted_hours,
                competencies,
                [shift[0]],
            )
            # Is needed to set the decision variable back to 0
            set_x(state, t_covered_by_shift, e, shift[0], shift[1], 0)

        # if(len(employee_objective_functions.keys()) == 0):
        #   return repair_set

        max_value = max(employee_objective_functions.items(), key=itemgetter(1))[1]
        e = choice(
            [key for key, value in employee_objective_functions.items() if value == max_value]
        )

        destroy_set = [set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1)]
        repair_set.append((e, shift[0], shift[1]))


def get_negative_deviation_from_demand(competencies, state, time_periods):

    deviation_from_demand = -sum(
        min(0, state.soft_vars["deviation_from_ideal_demand"][c, t])
        for c in competencies
        for t in time_periods
    )
    return deviation_from_demand


def get_adjusted_shifts(shifts, competencies, state, t_covered_by_shift):

    adjusted_shifts = {
        (t1, v1): -sum(
            state.soft_vars["deviation_from_ideal_demand"][c, t]
            for c in competencies
            for t in t_covered_by_shift[t1, v1]
        )
        - v1
        for t1, v1 in shifts
    }
    return adjusted_shifts


def update_soft_variables(L_C_D, competencies, contracted_hours, days, employees_changed, saturdays,
                          shifts_at_day, shifts_in_week, state, time_periods_in_week, time_step,
                          weeks):
    delta_calculate_deviation_from_contracted_hours(
        state,
        employees_changed,
        contracted_hours,
        weeks,
        time_periods_in_week,
        competencies,
        time_step,
    )
    calculate_partial_weekends(state, employees_changed, shifts_at_day, saturdays)
    calculate_isolated_working_days(state, employees_changed, shifts_at_day, days)
    calculate_isolated_off_days(state, employees_changed, shifts_at_day, days)
    calculate_consecutive_days(state, employees_changed, shifts_at_day, L_C_D, days)
    calculate_weekly_rest(state, shifts_in_week, employees_changed, weeks)


def update_hard_variables(competencies, days, demand, destroy_set, employee_with_competencies,
                          employees_changed, shifts_at_day, shifts_overlapping_t, state,
                          t_covered_by_shift):

    cover_multiple_demand_periods(state, destroy_set, t_covered_by_shift, competencies)
    more_than_one_shift_per_day(state, employees_changed, demand, shifts_at_day, days)
    above_maximum_demand(
        state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift
    )
    below_minimum_demand(
        state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift
    )
    mapping_shift_to_demand(
        state, destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies
    )


def should_stop_regret_search(deviation_from_demand, possible_employees, shift, state, weeks):
    condition = (deviation_from_demand < 6 or max([
            sum(state.soft_vars["deviation_contracted_hours"][e, j] for j in weeks)
            for e in possible_employees
        ])
            < shift[1]
    )

    return condition


def get_possible_employees(employees, shift, shifts_at_day, state):
    possible_employees = [
        e
        for e in employees
        if (sum(state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0
    ]
    return possible_employees


def get_deviation_from_contracted_hours(employees, shift, shifts_at_day, state, weeks):
    deviation_contracted_hours = {
        e: sum(state.soft_vars["deviation_contracted_hours"][e, j] for j in weeks)
        for e in employees
        if (sum(state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0
    }
    return deviation_contracted_hours
