from heapq import heappush, heappop, heapify
from pprint import pprint
from gurobipy import *
from loguru import logger
from utils.const import ALLOWED_SHIFT_DURATION
from heuristic.delta_calculations import delta_calculate_deviation_from_demand, \
    delta_calculate_negative_deviation_from_contracted_hours, calculate_weekly_rest, \
    calculate_partial_weekends, calculate_isolated_working_days, calculate_isolated_off_days, \
    calculate_consecutive_days, calc_weekly_objective_function, cover_multiple_demand_periods, \
    more_than_one_shift_per_day, above_maximum_demand, below_minimum_demand, \
    calculate_deviation_from_demand, regret_objective_function, mapping_shift_to_demand, \
    calculate_daily_rest_error, employee_shift_value, hard_constraint_penalties, \
    worst_employee_regret_value, f_regret_values, calculate_f
from operator import itemgetter
from heuristic.converter import set_x
from random import choice, choices


def week_demand_per_shift_repair(shifts_in_week, competencies, t_covered_by_shift, demand,
                       demand_per_shift, employees, contracted_hours, shifts_at_day,
                       time_step, time_periods_in_week, employee_with_competencies,
                       state, destroy_set, weeks):

    logger.warning(f"Using week_demand_repair for weeks {weeks}")
    # todo: use destroy_set for improvements

    repair_set = []
    employees_changed = employees
    number_of_employees = len(employees)

    for week in weeks:

        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed,
                                                                 contracted_hours, weeks,
                                                                 time_periods_in_week, competencies,
                                                                 time_step)
        shifts = shifts_in_week[week]
        demand_per_shift_in_week = {key: value for key, value in demand_per_shift.items()
                                    if key in shifts}

        employee_heap = get_scored_employees(employees, week, state, shifts_in_week)

        for _ in range(len(shifts)):

            # todo: How to make this work?
            #shift = max(demand_per_shift.items(), key=itemgetter(1))[0]

            shift = None
            max_demand = 0

            for s, d in demand_per_shift_in_week.items():
                if d > max_demand:
                    shift = s
                    max_demand = d

            logger.info(f"Repairing {shift} (d: {demand_per_shift[shift]})")

            considered_employees = []

            while demand_per_shift_in_week[shift] and number_of_employees > len(considered_employees):

                employee_score, employee = pop_from_heap(employee_heap)
                logger.trace(f"Employee {employee} (s: {employee_score}) chosen")
                updated_employee_score = employee_score

                if can_allocate(employee, shift, state, shifts_at_day):
                    repair_set.append(
                        set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1, None)
                    )

                    demand_per_shift_in_week[shift] -= 1

                    logger.trace(f"Allocating employee {employee} to shift {shift} "
                                 f"(remaining demand:{demand_per_shift_in_week[shift]})")

                    updated_employee_score -= shift[1]

                    logger.trace(f"Employee {employee} score: Original={employee_score}, "
                                 f"Updated={updated_employee_score}")

                considered_employees.append((updated_employee_score, employee))

            for employee_score, employee in considered_employees:
                push_to_heap(employee_heap, employee_score, employee)

    delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed,
                                                             contracted_hours, weeks,
                                                             time_periods_in_week, competencies,
                                                             time_step)

    calculate_deviation_from_demand(state, competencies, t_covered_by_shift,
                                    employee_with_competencies, demand, destroy_set)

    return repair_set


# todo: implement version to handle only parts of a week
def week_demand_repair(shifts_in_week, competencies, t_covered_by_shift,
                       demand, employees, contracted_hours, shifts_at_day,
                       time_step, time_periods_in_week, employee_with_competencies,
                       state, destroy_set, weeks):

    logger.warning(f"Using week_demand_repair for weeks {weeks}")
    # todo: use destroy_set for improvements

    repair_set = []
    employees_changed = employees
    number_of_employees = len(employees)

    for week in weeks:

        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed,
                                                                 contracted_hours, weeks,
                                                                 time_periods_in_week, competencies,
                                                                 time_step)

        remaining_demand = get_demand_for_week(competencies, demand, shifts_in_week,
                                               t_covered_by_shift, week)

        shift_heap = get_scored_shifts(shifts_in_week[week], t_covered_by_shift, remaining_demand)

        employee_heap = get_scored_employees(employees, week, state, shifts_in_week)
        number_of_shifts = len(shift_heap)

        for _ in range(number_of_shifts):

            shift, shift_score = get_most_valuable_shift(remaining_demand, shift_heap, t_covered_by_shift)
            allocations_needed = min([remaining_demand[t] for t in t_covered_by_shift[shift]])
            logger.info(f"Repairing shift {shift} (s: {shift_score}, d: {allocations_needed})")

            if not number_of_employees:
                logger.trace("There is no employee to cover the demand")
                continue
            if not allocations_needed:
                # TODO: This might cause problems. If there is one period with 0 demand and no
                #  other shift to cover it....
                logger.trace("The demand is already covered")
                continue

            considered_employees = []

            while allocations_needed and number_of_employees > len(considered_employees):

                employee_score, employee = pop_from_heap(employee_heap)
                logger.trace(f"Employee {employee} (s: {employee_score}) chosen")
                updated_employee_score = employee_score

                if can_allocate(employee, shift, state, shifts_at_day):
                    repair_set.append(
                        set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1, None)
                    )

                    for t in t_covered_by_shift[shift]:

                        remaining_demand[t] -= 1

                    allocations_needed -= 1

                    logger.trace(f"Allocating employee {employee} to shift {shift} "
                                 f"(remaining demand:{allocations_needed})")

                    updated_employee_score -= shift[1]

                    logger.trace(f"Employee {employee} score: Original={employee_score}, "
                                 f"Updated={updated_employee_score}")

                considered_employees.append((updated_employee_score, employee))

            for employee_score, employee in considered_employees:
                push_to_heap(employee_heap, employee_score, employee)

            # TODO: Need to find a way to update demand after each iteration
            shift_heap = get_scored_shifts(shifts_in_week[week], t_covered_by_shift,
                                           remaining_demand)

    delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed,
                                                             contracted_hours, weeks,
                                                             time_periods_in_week, competencies,
                                                             time_step)

    calculate_deviation_from_demand(state, competencies, t_covered_by_shift,
                                    employee_with_competencies, demand, destroy_set)

    return repair_set


def get_most_valuable_shift(remaining_demand, shift_heap, t_covered_by_shift):
    shift_score, shift = pop_from_heap(shift_heap)
    updated_shift_score = get_score_for_shift(shift, t_covered_by_shift, remaining_demand)
    #
    while shift_score != updated_shift_score:
        logger.trace(f"Outdated shift score {shift}: {shift_score} vs"
                     f" {updated_shift_score}")
        push_to_heap(shift_heap, updated_shift_score, shift)

        shift_score, shift = pop_from_heap(shift_heap)
        updated_shift_score = get_score_for_shift(shift, t_covered_by_shift, remaining_demand)
    return shift, shift_score


def get_demand_for_week(competencies, demand, shifts_in_week, t_covered_by_shift, week):
    times_in_shift_set = set()
    for shift in shifts_in_week[week]:
        times_in_shift_set.update(t_covered_by_shift[shift])
    remaining_demand = {t: sum(demand["min"][c, t] for c in competencies)
                        for t in times_in_shift_set}
    return remaining_demand


def can_allocate(employee, shift, state, shifts_at_day):

    return not any(
        [state.x[employee, t, v] for t, v in shifts_at_day[int(shift[0] / 24)]])


def get_scored_employees(employees, week, state, shifts_in_week):

    h = []

    for employee in employees:
        score = get_score_for_employee(employee, week, state, shifts_in_week)
        push_to_heap(h, score, employee)

    return h


def get_score_for_employee(employee, week, state, shifts_in_week):

    deviation_contracted = state.soft_vars["deviation_contracted_hours"][employee, week]

    # TODO: Include weekly rest?

    # TODO: set a better threshold here. Maybe 140% of contracted hours?
    # penalize negative deviation of contracted hours
    score = deviation_contracted if deviation_contracted > -10 else 100*deviation_contracted
    logger.trace(f"employee {employee}: dc={deviation_contracted}, s={score}")

    return score


def get_scored_shifts(shifts, t_covered_by_shift, remaining_demand):

    h = []

    # todo: pass shifts_at_week in as argument?

    for shift in shifts:
        score = get_score_for_shift(shift, t_covered_by_shift, remaining_demand)

        if score <= 0:
            # Shifts without demand is not relevant. Score is 0, but we dont want to work with it
            # further
            continue

        push_to_heap(h, score, shift)

    #breakpoint()
    return h


def get_score_for_shift(shift, t_covered_by_shift, remaining_demand):
    score = sum(remaining_demand[t] for t in t_covered_by_shift[shift]) - shift[1]
    return score


def pop_from_heap(h):

    # TODO: add docstring

    score, element = heappop(h)

    return -score, element


def push_to_heap(h, score, element):
    # all the scores are inverted to convert the heap to a max heap. The heap sorts on first
    # elements of the tuple

    heappush(h, (-score, element))


def get_demand_for_period(period, demand, competencies, demand_type="ideal"):
    return [demand[demand_type][c, t] for c in competencies for t in period]


def worst_week_repair(shifts_in_week, competencies, t_covered_by_shift, employee_with_competencies,
                      employee_with_competency_combination, demand, time_step, time_periods_in_week,
                      employees, contracted_hours, weeks, shifts_at_day, state, destroy_set, week):
    """
        A greedy repair operator based on destroying the worst week.
        The last three arguments are passed from its corresponding destroy operator.

        It finds the shift with highest deviation from demand.
        This shift is then assigned to the employee with highest deviation from contracted hours
        as long as that employee does not work on the day of the shift we are assigning. 

        It continues to do so until either the total negative deviation from demand is below a threshold (6)
        or we do not have any employees to assign to this shift as all employees are working this day 
    """
    repair_set = []
    employees_changed = employees
    changed = destroy_set.copy()
    impossible_shifts = []

    logger.info(f"Repairing week: {week}")

    while (True):
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift,
                                        employee_with_competencies, demand, changed)
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed,
                                                                 contracted_hours, weeks,
                                                                 time_periods_in_week, competencies,
                                                                 time_step)

        if sum(state.hard_vars["below_minimum_demand"].values()) != 0:
            shifts =    {
                        (t1, v1, comp): -sum(-state.hard_vars["below_minimum_demand"][c,t]
                                        for c in comp
                                        for t in t_covered_by_shift[t1, v1]
                                        if (c,t) in state.hard_vars["below_minimum_demand"])
                                        - (20*(len(comp)-1) + v1)
                                        for comp in employee_with_competency_combination 
                                        for t1, v1 in shifts_in_week[week[0]]
                                        if (t1,v1,comp) not in impossible_shifts
                        }
  


        else:
            shifts =    {
                        (t1, v1, comp): -sum(state.soft_vars["deviation_from_ideal_demand"][c,t]
                                        for c in comp
                                        for t in t_covered_by_shift[t1, v1]
                                        if (c,t) in state.soft_vars["deviation_from_ideal_demand"])
                                        - (20*(len(comp)-1) + v1)
                                        for comp in employee_with_competency_combination 
                                        for j in week
                                        for t1, v1 in shifts_in_week[j]
                                        if (t1,v1,comp) not in impossible_shifts
                        }

        best_shift_value = max(shifts.items(), key=itemgetter(1))[1]
        shift = choice([key for key, value in shifts.items() if value == best_shift_value])

        competency_pair = shift[2]

        deviation_from_demand = -sum(
            state.soft_vars["deviation_from_ideal_demand"][c, t]
            for c in competency_pair
            for t in t_covered_by_shift[shift[0], shift[1]]
            if (c, t) in state.soft_vars["deviation_from_ideal_demand"]
            if state.soft_vars["deviation_from_ideal_demand"][c, t] < 0
        )

        if deviation_from_demand <= ALLOWED_SHIFT_DURATION[0]/time_step:
            return repair_set

        y_s_1 = {
            t: {
                c: state.soft_vars["deviation_from_ideal_demand"][c, t]
                for c in competency_pair
                if (c, t) in state.soft_vars["deviation_from_ideal_demand"]
            }
            for t in t_covered_by_shift[shift[0], shift[1]]
        }

        y_s = [
            min(y_s_1[t].items(), key=itemgetter(1))[0]
            for t in t_covered_by_shift[shift[0], shift[1]]
            if len(y_s_1[t]) != 0
        ]
        competencies_needed = tuple(set(y_s))

        deviation_contracted_hours = {e:
                                          (sum(state.soft_vars["deviation_contracted_hours"][e, j]
                                               for j in weeks)

                                           - (competency_level - len(competencies_needed)))

                                          + (20 if (sum(
                                              state.soft_vars["deviation_contracted_hours"][e, j]
                                              for j in weeks) - shift[1] >= 8.5) else 0)

                                          + (20 if (sum(
                                              state.soft_vars["deviation_contracted_hours"][e, j]
                                              for j in weeks) - shift[1] <= 17) else 0)

                                          + (100 if (sum(
                                              state.soft_vars["deviation_contracted_hours"][e, j]
                                              for j in weeks) - shift[1] == 0) else 0)

                                      for (competency_level, e) in
                                      employee_with_competency_combination[competencies_needed]
                                      if (sum(state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0}

        if all(i <= ALLOWED_SHIFT_DURATION[0] for i in deviation_contracted_hours):
            impossible_shifts.append(shift)
            continue

        e = max(deviation_contracted_hours.items(), key=itemgetter(1))[0]

        repair_set.append(set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1, y_s))
        employees_changed = [e]
        changed = [(e, shift[0], shift[1])]


def worst_week_regret_repair(shifts_in_week, competencies, t_covered_by_shift,
                             employee_with_competencies, employee_with_competency_combination,
                             demand, time_step, time_periods_in_week, combined_time_periods_in_week,
                             employees, contracted_hours,
                             invalid_shifts, shift_combinations_violating_daily_rest,
                             shift_sequences_violating_daily_rest,
                             weeks, shifts_at_day, L_C_D, shifts_overlapping_t, preferences,
                             state, destroy_set, week):
    """
        The decision variables are set in the destroy operator. This only applies to the x and y variables as w now is a implisit variable that should be calculated
        At the beginning of a repair operator the soft variables and hard penalizing variables have not been updated to reflect the current changes to the decision variables

        To be able to calculate the deviation from demand (as this is how we choose a shift to assign) we would have to update the deviation from demand for the shifts (t_covered_by_shift) that have been destroyed.
        This is done efficiently in delta_calcualte_deviation_from_demand. It only checks the destroyed shifts (and their t's) and only in a negative direction (covering to much demand would give 0 in deviation)

        If the total deviation from demand (for the week/s in question) are below a threshold (6) we are satisfied and would return the repair_set with shifts (e,t,v) set

        If not we take the shift with highest deviation from demand (in the weeks in question) to be assigned. 
        We only search for an employee to assign to this shift based on if the employee are not working the day the shift is on.

        Which hard variables are important to calculate?:
            1.  Above/Below demand is done on a destroy_repair_set basis. This means we would have to calculate the above and below to get correct hard variables here if they were broken before the destroy fixes it. 
                A good thing here is that if we do so with the destroy_set we fix the entire week. This means we have a fresh start with no broken constraints this week.
            2.  More than one shift per day is calculated on a employee basis. It checks every day on that employee. This would have to be done before as we need it in the calculation. We cannot do this on each employee as we loop through them.
                We do have the days we would check though. Would also not need to do a calculation on these hard constraints, but rather just set them to 0. Most likely this is faster. 
            3.  Cover multiple demand periods are also done on a destroy_repair_set basis. It would have to be run before. 
            4.  Mapping shift to demand is also done on a destroy_repair_set basis. Would have to be run before to start fresh. 
            5.  Positive contracted hours. This is run together with negative contracted hours. This is done on a employee and week basis. By not running it before for all employees we would not have updated the contracted hours after the destroy when calculating the new objective function. 
                This would result in a wrong objective value. 
            6.  Weekly rest. When a week have been destroyed everyone starts with a full week of rest if calculated. If not we would continue with the rest they had before. The smartest move would be to start fresh here as well. 

        Which soft variables are important to calculate?:
            1. Partial weekend are only depending on the employee. It is calculated for every week no matter what as it is not based on destroy_repair_set
            2. The same is true for isolated working days, isolated off days and consecutive days

    """

    logger.info(f"Repairing week: {week}")

    repair_set = []
    # All employees gets changed in this operator atm. Employees changed are therefore set to all employees at the beginning.
    employees_changed = employees
    # Destroy_set is the shifts that have been destroyed.
    destroy_set = destroy_set.copy()
    saturdays = [5 + j * 7 for j in week]
    sundays = [6 + j * 7 for j in week]
    days = [i + (7 * j) for j in week for i in range(7)]
    impossible_shifts = []
    daily_destroy_and_repair = [destroy_set, []]
    while(True):
        #Initial phase to recalculate soft and hard variables of the destroyed weeks
        #Calculates deviation from demand first to see if we are done and can return
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        above_maximum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)

        if any(state.hard_vars["below_minimum_demand"].values()):
            shifts =    {
                        (t1, v1, comp): sum(state.hard_vars["below_minimum_demand"][c,t]
                                        for c in comp
                                        for t in t_covered_by_shift[t1, v1]
                                        if (c,t) in state.hard_vars["below_minimum_demand"])
                                        - (20*(len(comp)-1) + v1)
                                        for comp in employee_with_competency_combination 
                                        for t1, v1 in shifts_in_week[week[0]]
                                        if (t1,v1,comp) not in impossible_shifts
                        }          

        else:
            shifts =    {
                        (t1, v1, comp): -sum((10 if state.soft_vars["deviation_from_ideal_demand"][c, t] >= 0 else state.soft_vars["deviation_from_ideal_demand"][c, t])
                                        for c in comp
                                        for t in t_covered_by_shift[t1, v1]
                                        if (c,t) in state.soft_vars["deviation_from_ideal_demand"])
                                        - (20*(len(comp)-1) + v1)
                                        for comp in employee_with_competency_combination 
                                        for j in week
                                        for t1, v1 in shifts_in_week[j]
                                        if (t1,v1,comp) not in impossible_shifts
                        }

        best_shift_value = max(shifts.items(), key=itemgetter(1))[1]
        shift = choice([key for key, value in shifts.items() if value == best_shift_value])   
        #shift = max(shifts.items(), key=itemgetter(1))[0]

        deviation_from_demand = -sum(state.soft_vars["deviation_from_ideal_demand"][c, t]
                                     for c in shift[2]
                                     for t in t_covered_by_shift[shift[0], shift[1]]
                                     if (c, t) in state.soft_vars["deviation_from_ideal_demand"]
                                     if state.soft_vars["deviation_from_ideal_demand"][c, t] < 0)

        y_s_1 = {t: {(c): state.soft_vars["deviation_from_ideal_demand"][c, t] for c in shift[2] if
                     (c, t) in state.soft_vars["deviation_from_ideal_demand"]} for t in
                 t_covered_by_shift[shift[0], shift[1]]}
        y_s = [min(y_s_1[t].items(), key=itemgetter(1))[0] for t in
               t_covered_by_shift[shift[0], shift[1]] if len(y_s_1[t]) != 0]

        competencies_needed = tuple(set(y_s))

        possible_employees = [(e, score) for score, e in
                              employee_with_competency_combination[competencies_needed] if (sum(
                state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0]

        if len(possible_employees) == 0:
            impossible_shifts.append(shift)
            continue

        if(deviation_from_demand < (5 * 1/time_step) or max([sum(state.soft_vars["deviation_contracted_hours"][e[0],j] for j in weeks) for e in possible_employees]) < shift[1]):
            return repair_set


        #Soft Restrictions/Variables
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        calculate_partial_weekends(state, employees_changed, shifts_at_day, saturdays)
        calculate_isolated_working_days(state, employees_changed, shifts_at_day, days)
        calculate_isolated_off_days(state, employees_changed, shifts_at_day, days)
        calculate_consecutive_days(state, employees_changed, shifts_at_day, L_C_D, days)
        calculate_weekly_rest(state, shifts_in_week, employees_changed, week)
        calculate_daily_rest_error(state, daily_destroy_and_repair, invalid_shifts,
                                   shift_combinations_violating_daily_rest,
                                   shift_sequences_violating_daily_rest)


        objective_values = {}
        for e, score in possible_employees:
            competency_score = score - len(competencies_needed)
            objective_values[e] = employee_shift_value(state, e, shift, saturdays, sundays, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, shifts_in_week, weeks, shifts_at_day, week[0], L_C_D, preferences, competencies, t_covered_by_shift, competency_score)

        max_value = max(objective_values.items(), key=itemgetter(1))[1]
        employee = choice([key for key, value in objective_values.items() if value == max_value])
        repair_set.append(set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1, y_s))
        employees_changed = [employee]
        destroy_set = [(employee, shift[0], shift[1])]
        daily_destroy_and_repair = [[], destroy_set]


def worst_employee_repair(competencies, t_covered_by_shift, employee_with_competencies,
                          employee_with_competency_combination, demand, contracted_hours, weeks,
                          time_periods_in_week, time_step, all_shifts, shifts_at_day, state,
                          destroy_set, employees):
    """
        A greedy repair operator based on destroying the worst employee.
        The last three arguments are passed from its corresponding destroy operator.

        It finds the shift with highest deviation from demand.
        This shift is then assigned to the employee with highest deviation from contracted hours
        as long as that employee does not work on the day of the shift we are assigning. 
        The difference between this operator and the worst week is that we only look at the employees we have destroyed in the destroy operator

        It continues to do so until either the total negative deviation from demand is below a threshold (6)
        or we do not have any employees to assign to this shift as all employees are working this day 
    """

    logger.info(f"Repairing employees: {employees}")

    repair_set = []
    destroy_set = destroy_set.copy()
    employees_changed = employees
    allowed_competency_combinations =  {combination for combination in 
                                        employee_with_competency_combination for item in 
                                        employee_with_competency_combination[combination] for e in 
                                        employees_changed if e == item[1]}
    
    impossible_shifts = []
    while(True):
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)
        shifts =    {
                    (t1, v1, comp): -sum(state.soft_vars["deviation_from_ideal_demand"][c,t]
                                                    for c in comp
                                                    for t in t_covered_by_shift[t1, v1]
                                                    if (c,t) in state.soft_vars["deviation_from_ideal_demand"])
                                                    - (20*(len(comp)-1) + v1)
                                                    for comp in employee_with_competency_combination
                                                    for t1, v1 in all_shifts
                                                    if (t1, v1, comp) not in impossible_shifts
                    }
        if not any(shifts.values()):
            return repair_set
        best_shift_value = max(shifts.items(), key=itemgetter(1))[1]
        shift = choice([key for key, value in shifts.items() if value == best_shift_value])

        y_s = [
            min(
                {c: state.soft_vars["deviation_from_ideal_demand"][c, t] for c in shift[2]}.items(),
                key=itemgetter(1),
            )[0]
            for t in t_covered_by_shift[shift[0], shift[1]]
        ]
        competencies_needed = tuple(set(y_s))


        deviation_from_demand = -sum(state.soft_vars["deviation_from_ideal_demand"][c,t] 
                                    for competencies_2 in allowed_competency_combinations 
                                    for c in competencies_2 
                                    for t in t_covered_by_shift[shift[0], shift[1]] 
                                    if (c, t) in state.soft_vars["deviation_from_ideal_demand"] 
                                    if state.soft_vars["deviation_from_ideal_demand"][c,t] < 0)
        
        
        
        if(deviation_from_demand < ALLOWED_SHIFT_DURATION[0]/time_step):
            return repair_set

        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed,
                                                                 contracted_hours, weeks,
                                                                 time_periods_in_week, competencies,
                                                                 time_step)
        deviation_contracted_hours = {
            e: (
                    sum(state.soft_vars["deviation_contracted_hours"][e, j] for j in weeks)
                    - 10 * (competency_level - len(competencies_needed))
            )
            for (competency_level, e) in employee_with_competency_combination[competencies_needed]
            if (sum(state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0
            if e in employees
        }

        if all(i <= ALLOWED_SHIFT_DURATION[0] for i in deviation_contracted_hours):
            impossible_shifts.append(shift)
            continue

        e = max(deviation_contracted_hours.items(), key=itemgetter(1))[0]

        repair_set.append(set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1, y_s))
        employees_changed = [e]
        destroy_set = [(e, shift[0], shift[1])]


def worst_employee_regret_repair(competencies, t_covered_by_shift, employee_with_competencies,
                                 employee_with_competency_combination, demand,
                                 all_shifts, off_shifts, saturdays, days, L_C_D, weeks,
                                 shifts_at_day, shifts_in_week, contracted_hours,
                                 invalid_shifts, shift_combinations_violating_daily_rest,
                                 shift_sequences_violating_daily_rest,
                                 time_periods_in_week, time_step, shifts_overlapping_t, preferences,
                                 state, destroy_set, employees_changed):
    logger.info(f"Repairing employees: {employees_changed}")

    repair_set = []
    destroy_set = destroy_set.copy()
    allowed_competency_combinations = {combination for combination in
                                       employee_with_competency_combination for item in
                                       employee_with_competency_combination[combination] for e in
                                       employees_changed if e == item[1]}
    daily_destroy_and_repair = [destroy_set, []]
    impossible_shifts = []
    sundays = [6 + (7 * j) for j in weeks]
    while(True):
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)
        above_maximum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)


        if any(state.hard_vars["below_minimum_demand"].values()):
            shifts =    {
                        (t1, v1, comp): sum(state.hard_vars["below_minimum_demand"][c,t]
                                        for c in comp
                                        for t in t_covered_by_shift[t1, v1]
                                        if (c,t) in state.hard_vars["below_minimum_demand"])
                                        - (20*(len(comp)-1) + v1)
                                        for comp in employee_with_competency_combination
                                        for t1, v1 in all_shifts
                                        if (t1, v1, comp) not in impossible_shifts
                        }
        else:
            shifts =    {
                        (t1, v1, comp): -sum(state.soft_vars["deviation_from_ideal_demand"][c,t]
                                        for c in comp
                                        for t in t_covered_by_shift[t1, v1]
                                        if (c,t) in state.soft_vars["deviation_from_ideal_demand"])
                                        - (20*(len(comp)-1) + v1)
                                        for comp in employee_with_competency_combination
                                        for t1, v1 in all_shifts
                                        if (t1, v1, comp) not in impossible_shifts
                        }

        best_shift_value = max(shifts.items(), key=itemgetter(1))[1]
        shift = choice([key for key, value in shifts.items() if value == best_shift_value])

        y_s = [
            min(
                {c: state.soft_vars["deviation_from_ideal_demand"][c, t] for c in shift[2]}.items(),
                key=itemgetter(1),
            )[0]
            for t in t_covered_by_shift[shift[0], shift[1]]
        ]
        competencies_needed = tuple(set(y_s))

        deviation_from_demand = -sum(state.soft_vars["deviation_from_ideal_demand"][c,t]
                                    for competencies_2 in allowed_competency_combinations 
                                    for c in competencies_2 
                                    for t in t_covered_by_shift[shift[0], shift[1]] 
                                    if (c, t) in state.soft_vars["deviation_from_ideal_demand"] 
                                    if state.soft_vars["deviation_from_ideal_demand"][c,t] < 0)

        possible_employees = [(e, score) for score, e in
                              employee_with_competency_combination[competencies_needed] if (sum(
                state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0 if
                              e in employees_changed]

        if(deviation_from_demand/time_step < 5 or max([sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) for e in employees_changed]) < shift[1]):
            return repair_set

        if not possible_employees or max([sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) for e, score in possible_employees]) < shift[1]:
            impossible_shifts.append(shift)
            continue



        #Soft Restrictions/Variables
        # calculate_partial_weekends(state, employees_changed, shifts_at_day, saturdays)
        # calculate_isolated_working_days(state, employees_changed, shifts_at_day, days)
        # calculate_isolated_off_days(state, employees_changed, shifts_at_day, days)
        # calculate_consecutive_days(state, employees_changed, shifts_at_day, L_C_D, days)
        # calculate_weekly_rest(state, shifts_in_week, employees_changed, weeks)
        # calculate_daily_rest_error(state, daily_destroy_and_repair, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest)


        # When we have found which shift should be assigned we have to choose the employee to take this shift.
        # This time I am doing this by setting and removing instead of copy. 
        employee_objective_functions = {}
        daily_destroy = []
        for e, score in possible_employees:
            competency_score = score - len(competencies_needed)
            employee_objective_functions[e] = worst_employee_regret_value(state, e, shift, saturdays, sundays, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, shifts_in_week, weeks, shifts_at_day, days, L_C_D, preferences, competencies, t_covered_by_shift, competency_score)

        max_value = max(employee_objective_functions.items(), key=itemgetter(1))[1]
        e = choice(
            [key for key, value in employee_objective_functions.items() if value == max_value])

        destroy_set = [set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1, y_s)]
        repair_set.append((e, shift[0], shift[1]))
        daily_destroy_and_repair = [[], destroy_set]


def week_demand_based_repair_random(shifts_in_week, competencies, t_covered_by_shift,
                             employee_with_competencies, employee_with_competency_combination,
                             demand, time_step, time_periods_in_week, combined_time_periods_in_week,
                             employees, contracted_hours, shifts_with_demand, 
                             invalid_shifts, shift_combinations_violating_daily_rest,
                             shift_sequences_violating_daily_rest,
                             weeks, shifts_at_day, L_C_D, shifts_overlapping_t, preferences,
                             state, destroy_set, week):

    repair_set = []
    employees_changed = employees
    destroy_set = destroy_set.copy()
    saturdays = [5 + j * 7 for j in week]
    sundays = [6 + j * 7 for j in week]
    shifts = {shift: demand for shift, demand in shifts_with_demand.items() if shift in shifts_in_week[week[0]]}

    while(shifts):
        below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)

        shift = choices(list(shifts.keys()), weights=list(shifts.values()))[0]
        possible_employees = [(e, score) for score, e in
                              employee_with_competency_combination[(0,)] if (sum(
                state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0]
        
        if not possible_employees or max([sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) for e, score in possible_employees]) < shift[1]:
            del shifts[shift]
            if not any(shifts.keys()):
                return repair_set
            continue

        #Husker ikke om jeg kjørte denne med week eller weeks
        if(max([sum(state.soft_vars["deviation_contracted_hours"][e[0],j] for j in weeks) for e in possible_employees]) < shift[1]):
            return repair_set
        
        
        objective_values = {}
        for e, score in possible_employees:
            objective_values[e] = employee_shift_value(state, e, shift, saturdays, sundays, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, shifts_in_week, weeks, shifts_at_day, week[0], L_C_D, preferences, competencies, t_covered_by_shift, 0)

        max_value = max(objective_values.items(), key=itemgetter(1))[1]
        employee = choice([key for key, value in objective_values.items() if value == max_value])
        repair_set.append(set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1, None))
        employees_changed = [employee]
        destroy_set = [(employee, shift[0], shift[1])]
        shifts[shift] -= 1
        if shifts[shift] == 0:
            del shifts[shift]

        if sum(shifts.values()) == 0:
            return repair_set
    return shifts
    

def week_demand_based_repair_greedy(shifts_in_week, competencies, t_covered_by_shift,
                             employee_with_competencies, employee_with_competency_combination,
                             demand, time_step, time_periods_in_week, combined_time_periods_in_week,
                             employees, contracted_hours, shifts_with_demand, 
                             invalid_shifts, shift_combinations_violating_daily_rest,
                             shift_sequences_violating_daily_rest,
                             weeks, shifts_at_day, L_C_D, shifts_overlapping_t, preferences, 
                             state, destroy_set, week):

    repair_set = []
    employees_changed = employees
    destroy_set = destroy_set.copy()
    saturdays = [5 + j * 7 for j in week]
    sundays = [6 + j * 7 for j in week]
    shifts = {shift: demand for shift, demand in shifts_with_demand.items() if shift in shifts_in_week[week[0]]}
    while(shifts):
        below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)
        
        shift = max(shifts.items(), key=itemgetter(1))[0]
        
        possible_employees = [(e, score) for score, e in
                              employee_with_competency_combination[(0,)] if (sum(
                state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0]


        if not possible_employees or max([sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) for e, score in possible_employees]) < shift[1]:
            del shifts[shift]
            continue
    
        #Husker ikke om jeg kjørte denne med week eller weeks
        if(max([sum(state.soft_vars["deviation_contracted_hours"][e[0],j] for j in weeks) for e in possible_employees]) < shift[1]):
            return repair_set
        
        
        objective_values = {}
        for e, score in possible_employees:
            objective_values[e] = employee_shift_value(state, e, shift, saturdays, sundays, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, shifts_in_week, weeks, shifts_at_day, week[0], L_C_D, preferences, competencies, t_covered_by_shift, 0)

        max_value = max(objective_values.items(), key=itemgetter(1))[1]
        employee = choice([key for key, value in objective_values.items() if value == max_value])
        repair_set.append(set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1, None))
        employees_changed = [employee]
        destroy_set = [(employee, shift[0], shift[1])]
        shifts[shift] -= 1
        if shifts[shift] == 0:
            del shifts[shift]

        if sum(shifts.values()) == 0:
            return repair_set
    return repair_set
        

def mip_week_operator_2(  employees, shifts_in_week, competencies, time_periods_in_week, combined_time_periods_in_week, 
                        employees_with_competencies, shifts_per_day, shifts_overlapping_t, t_in_off_shifts,
                         invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest,
                         weeks, time_step, demand, days, weights, contracted_hours, t_covered_by_shift, L_C_D, preferences,
                         state, destroy_set, week):

    days_in_week = days[7*week[0]:(week[0]+1)*7]
    delta_calculate_negative_deviation_from_contracted_hours(state, employees, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
    updated_contracted_hours = min(sum(contracted_hours[e] for e in employees), sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks for e in employees))

    model = Model(name="week_operator")
    y_dict = {(c, t): 0 for c in competencies for t in time_periods_in_week[c, week[0]]}
    plus = {(c, t): 0 for c in competencies for t in time_periods_in_week[c, week[0]]}
    minus = {(c, t): 0 for c in competencies for t in time_periods_in_week[c, week[0]]}
    mu = {(c, t): 0 for c in competencies for t in time_periods_in_week[c, week[0]]}
    x_dict = {(t,v): 0 for c in competencies for t_1 in time_periods_in_week[c, week[0]] for t,v in shifts_overlapping_t[t_1]}

    x = model.addVars(x_dict, vtype=GRB.INTEGER, name="x")
    mu = model.addVars(mu, vtype=GRB.INTEGER, name="mu")
    y = model.addVars(y_dict, vtype=GRB.INTEGER, name="y")
    delta_plus = model.addVars(plus, vtype=GRB.INTEGER, name="delta_plus")
    delta_minus = model.addVars(minus, vtype=GRB.INTEGER, name="delta_minus")


    model.addConstrs(
        (   y[c, t]
            == demand["min"][c, t] + mu[c, t]
            for c in competencies
            for t in time_periods_in_week[c, week[0]]
        ), name="minimum_demand_coverage")

    model.addConstrs(
        (
            mu[c, t] <= demand["max"][c, t] - demand["min"][c, t]
            for c in competencies
            for t in time_periods_in_week[c, week[0]]
        ),
        name="mu_less_than_difference")

    model.addConstrs(
        (   mu[c, t] + demand["min"][c, t] - demand["ideal"][c, t]
            == delta_plus[c, t] - delta_minus[c, t]
            for c in competencies
            for t in time_periods_in_week[c, week[0]]
        ), name="deviation_from_ideal_demand")


    model.addConstrs(
        (   quicksum(x[t_marked, v] for t_marked, v in shifts_overlapping_t[t])
            == quicksum(y[c, t] for c in competencies if y.get((c, t)))
            for t in combined_time_periods_in_week[week[0]]
        ), name="mapping_shift_to_demand")
    
    model.addConstrs((
        quicksum(x[t, v] for t, v in shifts_per_day[i]) <= len(employees)
        for i in days_in_week
    ), name="No_more_than_employees_shift_per_day")

    # model.addConstr(
    #     quicksum(
    #         v * x[t, v] for t, v in shifts_in_week[week[0]]
    #         ) <= updated_contracted_hours
    #     , name="less_than_contracted_hours"
    # )

    model.setObjective(
    quicksum(
        quicksum(delta_plus[c, t] + delta_minus[c, t]
                for t in time_periods_in_week[c, week[0]])
        for c in competencies
    )
    ,GRB.MINIMIZE,)

    #model.setParam("MipFocus", 1)
    model.setParam("TimeLimit", 10)
    model.optimize()

    shifts = {(t,v): x[t,v].x for t,v in shifts_in_week[week[0]] if x[t,v].x > 0}
    saturdays = [5 + 7*week[0]]
    sundays = [6 + 7*week[0]]
    repair_set = []
    while shifts.keys():
        
        #shift = max(shifts.items(), key=itemgetter(1))[0]
        shift = choices(list(shifts.keys()), weights=list(shifts.values()))[0]
        possible_employees = [e for e in employees if sum(state.x[e, t, v] for t, v in shifts_per_day[int(shift[0] / 24)]) == 0]
        if not possible_employees:
            del shifts[shift]
            continue

        shifts[shift] -= 1
        objective_values = {}
        for e in possible_employees:
            objective_values[e] = employee_shift_value(state, e, shift, saturdays, sundays, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, shifts_in_week, weeks, shifts_per_day, week[0], L_C_D, preferences, competencies, t_covered_by_shift,  0)

        max_value = max(objective_values.items(), key=itemgetter(1))[1]
        employee = choice([key for key, value in objective_values.items() if value == max_value])
        repair_set.append(set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1))

        employees_changed = [employee]

        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        
        if shifts[shift] == 0:
                del shifts[shift]
        
    return repair_set








def repair_week_based_on_f_values(shifts_in_week, competencies, t_covered_by_shift,
                             employee_with_competencies, employee_with_competency_combination,
                             demand, time_step, time_periods_in_week, combined_time_periods_in_week,
                             employees, contracted_hours,
                             invalid_shifts, shift_combinations_violating_daily_rest,
                             shift_sequences_violating_daily_rest,
                             weeks, shifts_at_day, L_C_D, shifts_overlapping_t, 
                             weights, preferences, shifts_with_demand,
                             all_saturdays, all_days,
                             state, destroy_set, week):
    """
        The decision variables are set in the destroy operator. This only applies to the x and y variables as w now is a implisit variable that should be calculated
        At the beginning of a repair operator the soft variables and hard penalizing variables have not been updated to reflect the current changes to the decision variables

        To be able to calculate the deviation from demand (as this is how we choose a shift to assign) we would have to update the deviation from demand for the shifts (t_covered_by_shift) that have been destroyed.
        This is done efficiently in delta_calcualte_deviation_from_demand. It only checks the destroyed shifts (and their t's) and only in a negative direction (covering to much demand would give 0 in deviation)

        If the total deviation from demand (for the week/s in question) are below a threshold (6) we are satisfied and would return the repair_set with shifts (e,t,v) set

        If not we take the shift with highest deviation from demand (in the weeks in question) to be assigned. 
        We only search for an employee to assign to this shift based on if the employee are not working the day the shift is on.

        Which hard variables are important to calculate?:
            1.  Above/Below demand is done on a destroy_repair_set basis. This means we would have to calculate the above and below to get correct hard variables here if they were broken before the destroy fixes it. 
                A good thing here is that if we do so with the destroy_set we fix the entire week. This means we have a fresh start with no broken constraints this week.
            2.  More than one shift per day is calculated on a employee basis. It checks every day on that employee. This would have to be done before as we need it in the calculation. We cannot do this on each employee as we loop through them.
                We do have the days we would check though. Would also not need to do a calculation on these hard constraints, but rather just set them to 0. Most likely this is faster. 
            3.  Cover multiple demand periods are also done on a destroy_repair_set basis. It would have to be run before. 
            4.  Mapping shift to demand is also done on a destroy_repair_set basis. Would have to be run before to start fresh. 
            5.  Positive contracted hours. This is run together with negative contracted hours. This is done on a employee and week basis. By not running it before for all employees we would not have updated the contracted hours after the destroy when calculating the new objective function. 
                This would result in a wrong objective value. 
            6.  Weekly rest. When a week have been destroyed everyone starts with a full week of rest if calculated. If not we would continue with the rest they had before. The smartest move would be to start fresh here as well. 

        Which soft variables are important to calculate?:
            1. Partial weekend are only depending on the employee. It is calculated for every week no matter what as it is not based on destroy_repair_set
            2. The same is true for isolated working days, isolated off days and consecutive days

    """

    logger.info(f"Repairing week: {week}")

    repair_set = []
    # All employees gets changed in this operator atm. Employees changed are therefore set to all employees at the beginning.
    employees_changed = employees
    # Destroy_set is the shifts that have been destroyed.
    destroy_set = destroy_set.copy()
    saturdays = [5 + j * 7 for j in week]
    sundays = [6 + j * 7 for j in week]
    days = [i + (7 * j) for j in week for i in range(7)]
    impossible_shifts = []
    daily_destroy_and_repair = [destroy_set, []]
    
    shifts = {shift: demand for shift, demand in shifts_with_demand.items() if shift in shifts_in_week[week[0]]}

    
    while(shifts):

        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        #calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)

        shift = choices(list(shifts.keys()), weights=list(shifts.values()))[0]


        possible_employees = [e for e in employees if (sum(state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0 and sum(state.soft_vars["deviation_contracted_hours"][e, j] for j in weeks) > 5]

        if len(possible_employees) == 0:
            for shift in shifts_at_day[int(shift[0]/24)]:
                shifts.pop(shift, None)
            continue


        #Soft Restrictions/Variables
        calculate_partial_weekends(state, employees_changed, shifts_at_day, saturdays)
        calculate_isolated_working_days(state, employees_changed, shifts_at_day, days)
        calculate_isolated_off_days(state, employees_changed, shifts_at_day, days)
        calculate_consecutive_days(state, employees_changed, shifts_at_day, L_C_D, days)
        calculate_weekly_rest(state, shifts_in_week, employees_changed, week)
        calculate_daily_rest_error(state, daily_destroy_and_repair, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest)

        calculate_f(state, employees_changed, all_saturdays, all_days, L_C_D, weeks, weights, preferences, competencies)
        #print("Initial f-values: " + str(state.f))
        value = {}
        for e in possible_employees:
            updated_f = state.f.copy()
            f_diff, penalties = f_regret_values(state, e, shift, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, weeks, saturdays, sundays, days, shifts_in_week, shifts_at_day, weights, preferences, t_covered_by_shift, L_C_D)
            updated_f[e] += f_diff

            value[e] = sum(updated_f.values()) + len(employees) * 0.1 * min(updated_f.values()) + 10 * penalties
        #print(value)
        max_value = max(value.items(), key=itemgetter(1))[1]
        employee = choice([key for key, value in value.items() if value == max_value])

        repair_set.append(set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1))
        employees_changed = [employee]
        destroy_set = [(employee, shift[0], shift[1])]
        daily_destroy_and_repair = [[], destroy_set]

        shifts[shift] -= 1
        if shifts[shift] == 0:
            del shifts[shift]
        #print()
    return repair_set





"""
    Tanker til ny operator:
    Skiftene må enten komme fra demand eller grådig. 
    Det beste her vil nok være å velge det lengste skiftet som har demand hele sin periode fra skiftene gitt av SDP. Dette skal være de optimale skiftene og derfor burde brukes. Teoretisk sett skal man ikke behove å sjekke demand ettersom de skal være opptimale til å dekke demand.
    Det som derimot er vanskelig er at hvis et man ikke har nok kontraktsfestede timer til å dekke dette skiftet så burde man velge det lengste skiftet som fortsatt dekker demand i hele sin periode.
    I alle tilfeller hvor vi har ekstra kontraktsfestede timer så vil det ikke ha noe å si. I rproblem3 derimot vil man ofte få problem med å dekke skiftene pga kontraktsfestede timer. 

    Valget av ansatte bør gjøres på bakgrunn av f- og g-verdier. Man tar da å velger den ansatte som gir best total f + g verdi (Dette vil si best økning i sin f-verdi samtidig som g-en tilfredstilles. )
"""



def mip_week_operator_3(    employees, shifts_in_week, competencies, time_periods_in_week, combined_time_periods_in_week, 
                            employees_with_competencies, shifts_per_day, shifts_overlapping_t, t_in_off_shifts,
                            invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest,
                            weeks, time_step, demand, days, weights, contracted_hours, t_covered_by_shift, shifts_with_demand, L_C_D, preferences, 
                            state, destroy_set, week):

    days_in_week = days[7*week[0]:(week[0]+1)*7]
    delta_calculate_negative_deviation_from_contracted_hours(state, employees, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
    updated_contracted_hours = {e: sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) for e in employees}
    
    sunday = [days_in_week[-1]]
    saturday = [days_in_week[-2]]

    model = Model(name="week_operator_2")
    y_dict = {(c, e, t): 0 for c in competencies for e in employees for t in time_periods_in_week[c, week[0]]}
    plus = {(c, t): 0 for c in competencies for t in time_periods_in_week[c, week[0]]}
    minus = {(c, t): 0 for c in competencies for t in time_periods_in_week[c, week[0]]}
    mu = {(c, t): 0 for c in competencies for t in time_periods_in_week[c, week[0]]}
    x_dict = {(e,t,v): 0 for e in employees for c in competencies for t_1 in time_periods_in_week[c, week[0]] for t,v in shifts_overlapping_t[t_1]}
    #x_dict = {(e,t,v): 0 for e in employees for c in competencies for t_1 in time_periods_in_week[c, week[0]] for t,v in shifts_overlapping_t[t_1] if (t, v) in shifts_with_demand}
    updated_demand = {
        "min": {(c,t): demand["min"][c,t] - sum(state.y[c,e,t] for e in employees) for c in competencies for t in time_periods_in_week[c, week[0]]},
        "ideal": {(c,t): demand["ideal"][c,t] - sum(state.y[c,e,t] for e in employees) for c in competencies for t in time_periods_in_week[c, week[0]]},
        "max": {(c,t): demand["max"][c,t] - sum(state.y[c,e,t] for e in employees) for c in competencies for t in time_periods_in_week[c, week[0]]}
    }
    x = model.addVars(x_dict, vtype=GRB.BINARY, name="x")
    mu = model.addVars(mu, vtype=GRB.INTEGER, name="mu")
    y = model.addVars(y_dict, vtype=GRB.BINARY, name="y")
    delta_plus = model.addVars(plus, vtype=GRB.CONTINUOUS, name="delta_plus")
    delta_minus = model.addVars(minus, vtype=GRB.CONTINUOUS, name="delta_minus")
    lam_plus = model.addVars(employees, vtype=GRB.CONTINUOUS, name="Lambda_plus")
    lam_minus = model.addVars(employees, vtype=GRB.CONTINUOUS, name="Lambda_minus")
    rho_sat = model.addVars(employees, saturday, vtype=GRB.BINARY, name="rho_sat")
    rho_sun = model.addVars(employees, sunday, vtype=GRB.BINARY, name="rho_sun")
    iso_work = model.addVars(employees, days_in_week, vtype=GRB.BINARY, name="q_iso_work")
    iso_off = model.addVars(employees, days_in_week, vtype=GRB.BINARY, name="q_iso_off")
    gamma = model.addVars(employees, days_in_week, vtype=GRB.BINARY, name="gamma")
    con = model.addVars(employees, days_in_week[:-L_C_D], vtype=GRB.BINARY, name="consecutive_days")
    g = model.addVar(vtype=GRB.CONTINUOUS, name="lowest_contracted_hours")

    model.addConstrs(
        (   quicksum(y[c, e, t] for e in employees_with_competencies[c])
            == updated_demand["min"][c, t] + mu[c, t]
            for c in competencies
            for t in time_periods_in_week[c, week[0]]
        ), name="minimum_demand_coverage")
    
    model.addConstrs(
        (   mu[c, t] <= updated_demand["max"][c, t] - updated_demand["min"][c, t]
            for c in competencies
            for t in time_periods_in_week[c, week[0]]
        ),
        name="mu_less_than_difference")

    model.addConstrs(
        (   mu[c, t] + updated_demand["min"][c, t] - updated_demand["ideal"][c, t]
            == delta_plus[c, t] - delta_minus[c, t]
            for c in competencies
            for t in time_periods_in_week[c, week[0]]
        ), name="deviation_from_ideal_demand")


    model.addConstrs(
        (   quicksum(x[e, t_marked, v] for t_marked, v in shifts_overlapping_t[t])
            == quicksum(y[c, e, t] for c in competencies if y.get((c,e,t)))
            for e in employees
            for t in time_periods_in_week[0, week[0]]
        ), name="mapping_shift_to_demand")

    model.addConstrs(
        (
            quicksum(x[e, t, v] for t, v in shifts_per_day[i]) <= 1
            for e in employees
            for i in days_in_week
        ), name="cover_maximum_one_shift",
    )

    model.addConstrs(
        (   quicksum(x[e, t, v] for t, v in shifts_in_week[week[0]]) <= 6
            for e in employees
        ), name="max_6_shifts_a_week",
    )
    
    # model.addConstrs(
    #     (   quicksum(
    #             quicksum(time_step * y[c, e, t] for t in time_periods_in_week[c, week[0]])
    #             for c in competencies)
    #         + lam[e] == updated_contracted_hours[e]
    #         for e in employees
    #     ), name="contracted_hours")
    
    model.addConstrs(
        (   quicksum(time_step * y[c, e, t] for c in competencies for t in time_periods_in_week[c, week[0]]) == updated_contracted_hours[e] + lam_plus[e] - lam_minus[e]
            for e in employees
        ), name="contracted_hours")

    model.addConstrs(
        (   gamma[e, i] - gamma[e, i + 1] == rho_sat[e, i] - rho_sun[e, i + 1]
            for e in employees
            for i in saturday
        ), name="partial_weekends")

    model.addConstrs(
        (   gamma[e, i] - gamma[e, (i + 1)] + gamma[e, (i + 2)] - 1 <= iso_off[e, (i + 1)]
            for e in employees
            for i in days_in_week[:-2]
        ), name="isolated_off_days")
    
    model.addConstrs(
        (   -gamma[e, i] + gamma[e, (i + 1)] - gamma[e, (i + 2)] <= iso_work[e, (i + 1)]
            for e in employees
            for i in days_in_week[:-2]
        ), name="isolated_working_days")

    model.addConstrs(
        (   quicksum(gamma[e, i_marked] for i_marked in range(i, i + L_C_D + 1)) - L_C_D
                <= con[e, i] - 1
                for e in employees
                for i in days_in_week[:-L_C_D]
            ), name="consecutive_days")

    model.addConstrs(
        (   quicksum(x[e, t, v] for t, v in shifts_per_day[i]) == gamma[e, i]
            for e in employees
            for i in days_in_week
        ), name="if_employee_e_works_day_i")

    model.addConstrs(
        g >= lam_minus[e] for e in employees
    )
    model.setObjective(
        quicksum(
                - weights["partial weekends"] * quicksum(rho_sat[e, i] + rho_sun[e, i + 1] for i in saturday)
                - weights["isolated working days"] * quicksum(iso_work[e, i] for i in days_in_week)
                - weights["isolated off days"] * quicksum(iso_off[e, i] for i in days_in_week)
                - weights["consecutive days"] * quicksum(con[e, i] for i in days_in_week[:-L_C_D])
                + weights["preferences"] * quicksum(preferences[e][t] * quicksum(y[c, e, t] for c in competencies) for t in time_periods_in_week[0, week[0]])
                - lam_plus[e]
                - g
        for e in employees)
        - quicksum(delta_plus[c, t] + delta_minus[c, t] for c in competencies for t in time_periods_in_week[c, week[0]])
    , GRB.MAXIMIZE)


    
    #model.setParam("MIPFocus", 1)
    model.setParam("TimeLimit", 5)
    model.optimize()
    model.write("answer_problem7.sol")
    repair_set = [set_x(state, t_covered_by_shift, e, t, v, 1) for e, t, v in x if abs(x[e,t,v].x) == 1]
    return repair_set
