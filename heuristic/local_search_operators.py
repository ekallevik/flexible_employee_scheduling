from collections import defaultdict
from pprint import pprint

from loguru import logger

from heuristic.delta_calculations import (
    calc_weekly_objective_function,
    calculate_consecutive_days,
    calculate_isolated_off_days,
    calculate_isolated_working_days,
    calculate_partial_weekends,
    calculate_weekly_rest,
    delta_calculate_negative_deviation_from_contracted_hours,
    employee_shift_value,
    worst_employee_regret_value,
    calculate_deviation_from_demand
)
from heuristic.converter import set_x, remove_x
from operator import itemgetter
from random import choice
from utils.const import DESIRED_SHIFT_DURATION
import itertools

from utils.heap import push_to_max_heap, pop_from_max_heap


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
        if state.hard_vars["weekly_off_shift_error"][emp, j] == 1:
            shifts = [(t, v) for t, v in shifts_in_week[j] if state.x[emp, t, v] != 0]
            days_in_week = [i + (7 * j) for i in range(7)]
            saturdays = [5 + (j * 7)]
            sundays = [6 + (j * 7)]
            objective_values = {}
            for shift in shifts:
                current_state = state.copy()
                possible_employees = [e for e in employees if sum(
                    current_state.x[e, t, v] for t, v in
                    shifts_at_day[int(shift[0] / 24)]) == 0 and (
                                      e, j) not in already_fixed_employees]

                set_x(current_state, t_covered_by_shift, emp, shift[0], shift[1], 0)

                calculate_weekly_rest(current_state, shifts_in_week, [emp], [j])
                calculate_partial_weekends(current_state, [emp], shifts_at_day, saturdays)
                calculate_isolated_working_days(current_state, [emp], shifts_at_day, days_in_week)
                calculate_isolated_off_days(current_state, [emp], shifts_at_day, days_in_week)
                calculate_consecutive_days(current_state, [emp], shifts_at_day, L_C_D, days_in_week)
                delta_calculate_negative_deviation_from_contracted_hours(current_state, [emp],
                                                                         contracted_hours, weeks,
                                                                         time_periods_in_week,
                                                                         competencies, time_step)

                # if sum(state.soft_vars["contracted_hours"][e,j] for j in weeks) - shift[1] >= 0
                if len(possible_employees) == 0:
                    print("Not enough employees")

                for e_p in possible_employees:
                    objective_values[e_p, shift] = employee_shift_value(state, e_p, shift,
                                                                        saturdays, sundays,
                                                                        invalid_shifts,
                                                                        shift_combinations_violating_daily_rest,
                                                                        shift_sequences_violating_daily_rest,
                                                                        shifts_in_week, weeks,
                                                                        shifts_at_day, j, 0)

            max_value = max(objective_values.items(), key=itemgetter(1))[1]
            employee = choice(
                [key for key, value in objective_values.items() if value == max_value])

            already_fixed_employees.append((emp, j))

            repair_set.append(
                set_x(state, t_covered_by_shift, employee[0], employee[1][0], employee[1][1], 1))
            destroy_set.append(
                remove_x(state, t_covered_by_shift, competencies, emp, employee[1][0],
                         employee[1][1]))

    return destroy_set, repair_set


def illegal_contracted_hours(state, shifts, time_step, employees, shifts_in_day, weeks,
                             t_covered_by_shift, contracted_hours, time_periods_in_week,
                             competencies):
    destroy_set = []
    repair_set = []
    delta_calculate_negative_deviation_from_contracted_hours(state, employees, contracted_hours,
                                                             weeks, time_periods_in_week,
                                                             competencies, time_step)
    for e in state.hard_vars["delta_positive_contracted_hours"]:
        if state.hard_vars["delta_positive_contracted_hours"][e] > 0:
            illegal_hours = state.hard_vars["delta_positive_contracted_hours"][e]
            illegal_shifts = [(e, t, v) for t, v in shifts if state.x[e, t, v] == 1]
            for e, t, v in illegal_shifts:
                swap_shifts = [(e, t1, v1) for e in employees for t1, v1 in
                               shifts_in_day[int(t / 24)] if
                               state.x[e, t1, v1] == 1 and v1 < v and sum(
                                   state.soft_vars["deviation_contracted_hours"][e, j] for j in
                                   weeks) + (v1 - v) >= 0]
                if (len(swap_shifts) != 0):
                    zero_shifts = [(e_2, t_2, v_2) for e_2, t_2, v_2 in swap_shifts if
                                   (v - v_2) == illegal_hours]
                    shift = min(swap_shifts, key=itemgetter(1)) if len(
                        zero_shifts) == 0 else choice(zero_shifts)
                    # shift = choice(swap_shifts)
                    destroy_set.append(remove_x(state, t_covered_by_shift, competencies, e, t, v))
                    destroy_set.append(
                        remove_x(state, t_covered_by_shift, competencies, shift[0], shift[1],
                                 shift[2]))

                    repair_set.append(set_x(state, t_covered_by_shift, e, shift[1], shift[2], 1))
                    repair_set.append(set_x(state, t_covered_by_shift, shift[0], t, v, 1))
                    delta_calculate_negative_deviation_from_contracted_hours(state, employees,
                                                                             contracted_hours,
                                                                             weeks,
                                                                             time_periods_in_week,
                                                                             competencies,
                                                                             time_step)
                    illegal_hours -= (v - shift[2])

                    if (illegal_hours <= 0):
                        break

    return destroy_set, repair_set


def reduce_overstaffing(state, shifts, employees, weeks, t_covered_by_shift, competencies,
                        combined_time_periods_in_week, time_step, shifts_covering_t):
    destroy_set = []
    repair_set = []

    #logger.warning(f"Reducing overstaffing from current level:
    # {sum(state.hard_vars['above_maximum_demand'].values())}")
    print()

    overstaffed = {t: sum(state.hard_vars["above_maximum_demand"][c, t]
                          for c in competencies
                          if state.hard_vars["above_maximum_demand"].get((c, t)))
                   for j in weeks
                   for t in combined_time_periods_in_week[j]
                   if sum(state.hard_vars["above_maximum_demand"][c, t]
                          for c in competencies
                          if state.hard_vars["above_maximum_demand"].get((c, t))) > 0
                   }

    #pprint(overstaffed)

    for t, excess in overstaffed.items():
        logger.info(f"Fix overstaffing for t={t}, excess={excess}")

        current_offset = time_step
        chosen_shift = None
        related_excess = {}
        impossible_shifts = set(shifts_covering_t[t])

        # note: this can contain impossible sets
        potential_shifts = set()

        # todo: maybe improve this?
        while current_offset <= 5:

            related_excess_exists = False

            following_shifts = shifts_covering_t[t + current_offset]
            potential_shifts.update(following_shifts)

            previous_shifts = shifts_covering_t[t - current_offset]
            potential_shifts.update(previous_shifts)

            if t + current_offset in overstaffed.keys():
                related_excess[t + current_offset] = overstaffed[t + current_offset]
                logger.info(f"t={t + current_offset} contains excess={overstaffed[t + current_offset]}")
                related_excess_exists = True

            if t - current_offset in overstaffed.keys():
                related_excess[t - current_offset] = overstaffed[t - current_offset]
                logger.info(f"t={t - current_offset} contains excess={overstaffed[t - current_offset]}")
                related_excess_exists = True

            current_offset += time_step

            if related_excess_exists:
                #breakpoint()
                continue

            logger.trace(f"No shifts to swap to. Moving to next offset={current_offset}")

        # remove impossible shifts
        possible_shifts = potential_shifts - impossible_shifts

        max_excess_removal = 0
        chosen_shift = None

        if possible_shifts:
            logger.trace(f"Possible shifts for t in [{t-current_offset}, {t+current_offset}]")
            print()
            pprint(possible_shifts)
            print("\n\n")

            for shift in possible_shifts:
                time_periods = t_covered_by_shift[shift]
                excess_removal = sum(min(excess, overstaffed.get(t, 0)) for t in time_periods)

                if excess_removal >= max_excess_removal:
                    max_excess_removal = excess_removal
                    chosen_shift = shift

        logger.info(f"Chosen shift {chosen_shift} removes {max_excess_removal} excess")

        # todo: fix this
        if not chosen_shift:
            break

        #breakpoint()

        employee_taboo = []

        for _ in range(int(excess)):

            logger.info(f"Looking for {excess} employees")

            #breakpoint()

            # todo: use a regret-approach / estimation-approach? or sort?
            most_overworked_employee = None
            shift_to_remove = None
            largest_violation_of_contracted = 0

            if not shifts_covering_t[t]:
                logger.info("How is this possible??")
                breakpoint()

            for shift in shifts_covering_t[t]:
                for employee in employees:
                    # todo: is there an easier way to extract the relevant employees?
                    if (employee, shift[0], shift[1]) in state.x:

                        overwork = sum(
                            state.hard_vars["delta_positive_contracted_hours"].get((employee, j), 0)
                            for j in weeks)

                        # todo: use taboo?
                        if overwork >= largest_violation_of_contracted and employee not in employee_taboo:
                            most_overworked_employee = employee
                            shift_to_remove = shift
                            largest_violation_of_contracted = overwork

            logger.info(f"Swapping shift {shift_to_remove} with {chosen_shift} for employee"
                        f" {most_overworked_employee}")

            destroy_set.append(
                remove_x(state, t_covered_by_shift, competencies, most_overworked_employee,
                         shift_to_remove[0], shift_to_remove[1])
            )
            employee_taboo.append(most_overworked_employee)

            if chosen_shift:
                logger.trace(f"Allocating employee {most_overworked_employee} to shift "
                             f"{chosen_shift}")

                repair_set.append(
                    set_x(state, t_covered_by_shift, most_overworked_employee, chosen_shift[0],
                          chosen_shift[1], 1)
                )

            else:
                logger.trace(f"Could not find a shift to replace {shift_to_remove}")

            #breakpoint()

    #breakpoint()

    return destroy_set, repair_set
