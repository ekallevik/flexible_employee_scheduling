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
    employee_shift_value, calculate_deviation_from_demand, below_minimum_demand,
    above_maximum_demand,
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


def reduce_overstaffing_with_related_heap(state, shifts, demand, employees,
                                          employee_with_competencies, weeks,
                                          t_covered_by_shift,
                                   competencies,
                                   combined_time_periods_in_week, time_step, shifts_covering_t):

    print()
    logger.warning(f"Reducing overstaffing from current level: "
                   f"{sum(state.hard_vars['above_maximum_demand'].values())}")

    destroy_set = []
    repair_set = []

    overstaffed_times, understaffed_times = get_t_with_staffing_violations(
        combined_time_periods_in_week, competencies, state, weeks)

    overstaffed_heap = get_overstaffed_heap(overstaffed_times, understaffed_times, shifts_covering_t, t_covered_by_shift)

    while overstaffed_heap:

        print()

        estimated_score, overstaffed_shift = pop_from_max_heap(overstaffed_heap)
        actual_score = get_staffing_score_for_shift(overstaffed_times, understaffed_times, overstaffed_shift, t_covered_by_shift)

        while actual_score != estimated_score:

            # if the actual score is negative the shift is not beneficial anymore
            if actual_score > 0:
                push_to_max_heap(overstaffed_heap, actual_score, overstaffed_shift)

            if not overstaffed_heap:
                logger.critical("No more shifts")
                return destroy_set, repair_set

            estimated_score, overstaffed_shift = pop_from_max_heap(overstaffed_heap)
            actual_score = get_staffing_score_for_shift(overstaffed_times, understaffed_times,
                                                        overstaffed_shift, t_covered_by_shift)

        logger.info(f"Fixing overstaffed shift {overstaffed_shift} (score={actual_score})")

        replacement_shift_set = get_replacement_shift_set(overstaffed_shift, shifts_covering_t,
                                                          time_step, overstaffed_times)

        scored_replacement_shifts = get_scored_replacement_shifts(competencies, demand,
                                                                  overstaffed_shift, overstaffed_times,
                                                                  replacement_shift_set, state,
                                                                  t_covered_by_shift, understaffed_times)
        target_score = 1

        if not scored_replacement_shifts:
            # todo: need to find a better solution
            above = {t: violation for t, violation in state.hard_vars[
                'above_maximum_demand'].items() if violation}

            below = {t: violation for t, violation in state.hard_vars[
                'below_minimum_demand'].items() if violation}

            logger.info(f"No replacement shift exists for overstaffed shift {overstaffed_shift}")
            #breakpoint()
            if actual_score > 0:

                delta_understaffing_for_destroy = 0

                for t in t_covered_by_shift[overstaffed_shift]:
                    if t not in overstaffed_times and t not in understaffed_times:
                        # this could make understaffing worse
                        deviation = sum(
                            state.soft_vars["deviation_from_ideal_demand"][c, t] for c in
                            competencies)
                        allowed_deviation = sum(
                            demand["ideal"].get((c, t), 0) for c in competencies) \
                                            - sum(
                            demand["min"].get((c, t), 0) for c in competencies)

                        if deviation == allowed_deviation:
                            # deletion of overstaffed_shift will make understaffing worse
                            delta_understaffing_for_destroy -= 1


                destroy_score = actual_score + delta_understaffing_for_destroy

                # todo: gt or gte?
                if destroy_score > 0:
                    logger.trace(f"Destroying shift {overstaffed_shift} "
                                 f"(destroy_score={destroy_score})")
                    target_shift = None

                else:
                    logger.trace(f"Keeping shift {overstaffed_shift} "
                                 f"(destroy_score={destroy_score})")
                    continue
            else:
                continue
        else:
            target_score, target_shift = max(scored_replacement_shifts)

        if target_score <= 0:
            # todo: need to find a better solution
            above = {t: violation for t, violation in state.hard_vars[
                'above_maximum_demand'].items() if violation}

            below = {t: violation for t, violation in state.hard_vars[
                'below_minimum_demand'].items() if violation}

            logger.info(f"No positive replacement shift exists for overstaffed shift"
                        f" {overstaffed_shift}")
            #target_shift = None

            if actual_score > 0:

                delta_understaffing_for_destroy = 0

                for t in t_covered_by_shift[overstaffed_shift]:
                    if t not in overstaffed_times and t not in understaffed_times:
                        # this could make understaffing worse
                        deviation = sum(
                            state.soft_vars["deviation_from_ideal_demand"][c, t] for c in
                            competencies)
                        allowed_deviation = sum(
                            demand["ideal"].get((c, t), 0) for c in competencies) \
                                            - sum(
                            demand["min"].get((c, t), 0) for c in competencies)

                        if deviation == allowed_deviation:
                            # deletion of overstaffed_shift will make understaffing worse
                            delta_understaffing_for_destroy -= 1

                destroy_score = actual_score + delta_understaffing_for_destroy

                # todo: gt or gte?
                if destroy_score > 0:
                    logger.trace(f"Destroying shift {overstaffed_shift} "
                                 f"(destroy_score={destroy_score})")
                    target_shift = None

                else:
                    logger.trace(f"Keeping shift {overstaffed_shift} "
                                 f"(destroy_score={destroy_score})")
                    continue
            else:
                continue

        logger.warning(f"Swap increases objective value with {target_score}")

        relevant_employees = [employee for employee in employees
                              if (employee, overstaffed_shift[0], overstaffed_shift[1]) in state.x]

        if not relevant_employees:
            logger.critical("No more employees to allocate")
            break

        # todo: must make sure the employee can work the target_shift
        # todo: this can be improved
        chosen_employee = relevant_employees[0]

        destroy_set.append(
            remove_x(state, t_covered_by_shift, competencies, chosen_employee,
                     overstaffed_shift[0], overstaffed_shift[1])
        )
        logger.error(f"Employee {chosen_employee} removed from shift {overstaffed_shift}")

        if target_shift:
            repair_set.append(
                set_x(state, t_covered_by_shift, chosen_employee, target_shift[0],
                      target_shift[1], 1)
            )

            logger.error(f"Employee {chosen_employee} allocated to shift "
                         f"{target_shift}")

            destroy_repair_set = [destroy_set[-1], repair_set[-1]]
        else:
            destroy_repair_set = [destroy_set[-1]]

        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand,  destroy_repair_set)
        below_minimum_demand(state, destroy_repair_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        above_maximum_demand(state, destroy_repair_set, employee_with_competencies, demand, competencies, t_covered_by_shift)

        overstaffed_times, understaffed_times = get_t_with_staffing_violations(
            combined_time_periods_in_week, competencies, state, weeks)

        updated_score = get_staffing_score_for_shift(overstaffed_times, understaffed_times,
                                         overstaffed_shift, t_covered_by_shift)

        if updated_score <= 0:
            logger.trace(f"Shift {overstaffed_shift} does no longer violate maximum demand")
        elif updated_score >= actual_score:
            logger.trace(f"Could not remove excess demand from {overstaffed_shift}")
            #breakpoint()
        else:
            logger.warning(f"Shift {overstaffed_shift} now have score={actual_score}")
            push_to_max_heap(overstaffed_heap, actual_score, overstaffed_shift)

        if target_score <= 0:
            # todo: need to find a better solution
            above = {t: violation for t, violation in state.hard_vars[
                'above_maximum_demand'].items() if violation}

            below = {t: violation for t, violation in state.hard_vars[
                'below_minimum_demand'].items() if violation}

            logger.info(f"No positive replacement shift exists for overstaffed shift"
                        f" {overstaffed_shift}")
            target_shift = None
            #
            breakpoint()

    return destroy_set, repair_set


def get_overstaffed_heap(overstaffed_times, understaffed_times, shifts_covering_t,
                         t_covered_by_shift):

    overstaffed_shift_set = set()

    for t in overstaffed_times:
        shifts = shifts_covering_t[t]
        # todo: use update instead of add?
        for shift in shifts:
            overstaffed_shift_set.add(shift)

    overstaffed_heap = []

    for shift in overstaffed_shift_set:
        score = get_staffing_score_for_shift(overstaffed_times, understaffed_times, shift, t_covered_by_shift)
        # the shift needs to be beneficial
        if score > 0:
            logger.trace(f"Shift {shift} is a potential swap with score={score}")
            push_to_max_heap(overstaffed_heap, score, shift)

    return overstaffed_heap


def get_t_with_staffing_violations(combined_time_periods_in_week, competencies, state, weeks):
    understaffed_times = [t for j in weeks
                          for t in combined_time_periods_in_week[j]
                          if sum(state.hard_vars["below_minimum_demand"].get((c, t), 0)
                                 for c in competencies) > 0]

    overstaffed_times = [t for j in weeks
                         for t in combined_time_periods_in_week[j]
                         if sum(state.hard_vars["above_maximum_demand"].get((c, t), 0)
                                for c in competencies) > 0]
    return overstaffed_times, understaffed_times


def get_scored_replacement_shifts(competencies, demand, overstaffed_shift, overstaffed_times,
                                  replacement_shift_set, state, t_covered_by_shift,
                                  understaffed_times):
    replacement_shift_list = []
    for replacement_shift in replacement_shift_set:

        # positve values means increased quality
        delta_understaffing = 0
        delta_overstaffing = 0

        unique_t_for_overstaffed_shift, unique_t_for_replacement_shift = get_unique_t(
            overstaffed_shift, replacement_shift, t_covered_by_shift)

        for t in unique_t_for_overstaffed_shift:
            if t in understaffed_times:
                # this means one understaffed t will be removed
                delta_understaffing += 1
            if t in overstaffed_times:
                # this means one overstaffed t will be removed
                delta_overstaffing += 1

        for t in unique_t_for_replacement_shift:
            if t in understaffed_times:
                # this means one understaffed t will be introduced
                delta_understaffing -= 1
            else:
                # this could make understaffing worse
                deviation = sum(state.soft_vars["deviation_from_ideal_demand"][c, t] for c in
                                competencies)
                allowed_deviation = sum(demand["ideal"].get((c, t), 0) for c in competencies) \
                                    - sum(demand["min"].get((c, t), 0) for c in competencies)

                if deviation > allowed_deviation:
                    logger.critical("This should not be possible as it should be caught in "
                                    "previous if")
                    delta_understaffing -= 1000

                # this will lead to a new period with understaffing
                elif deviation == allowed_deviation:
                    delta_understaffing -= 1

            if t in overstaffed_times:
                # this means one overstaffed t will be introduced
                delta_overstaffing -= 1
            else:
                # this could make overstaffing worse
                deviation = sum(
                    state.soft_vars["deviation_from_ideal_demand"][c, t] for c in competencies)
                allowed_deviation = sum(demand["max"].get((c, t), 0) for c in competencies) \
                                    - sum(demand["ideal"].get((c, t), 0) for c in competencies)

                if deviation > allowed_deviation:
                    logger.critical("This should not be possible as it should be caught in "
                                    "previous if")
                    delta_overstaffing -= 1000
                # this will lead to a new period with understaffing
                elif deviation == allowed_deviation:
                    delta_overstaffing -= 1

        score = delta_understaffing + delta_overstaffing

        logger.info(f"Replacement shift {replacement_shift} has score {score}")

        # Only want to swap if replacement_shift is better than current shift
        if score > 0:
            replacement_shift_list.append((score, replacement_shift))
    return replacement_shift_list


def get_unique_t(overstaffed_shift, replacement_shift, t_covered_by_shift):
    relevant_times = set(t_covered_by_shift[replacement_shift] + t_covered_by_shift[
        overstaffed_shift])
    unique_t_for_overstaffed_shift = relevant_times - set(t_covered_by_shift[
                                                              replacement_shift])
    unique_t_for_replacement_shift = relevant_times - set(t_covered_by_shift[
                                                              overstaffed_shift])
    return unique_t_for_overstaffed_shift, unique_t_for_replacement_shift


def get_replacement_shift_set(overstaffed_shift, shifts_covering_t, time_step, overstaffed_times):

    replacement_shift_set = set()

    offset = 0
    start = overstaffed_shift[0] - offset
    end = overstaffed_shift[0] + overstaffed_shift[1] + offset

    # TODO: make the set more strict?
    #start = overstaffed_shift[0]
    #end = overstaffed_shift[0]

    current_time = start

    while current_time <= end:
        # logger.info(f"Looping over time={current_time}")
        for shift in shifts_covering_t[current_time]:
            replacement_shift_set.add(shift)
        # replacement_shift_set.update()
        current_time += time_step
    # remove the violating shift

    replacement_shift_set.remove(overstaffed_shift)

    return replacement_shift_set


def get_staffing_score_for_shift(overstaffed_times, understaffed_times, shift, t_covered_by_shift):

    # todo: introduce allowed deviation from demand here?
    score = 0
    for t in t_covered_by_shift[shift]:
        score += 1 if t in overstaffed_times else 0
        score -= 1 if t in understaffed_times else 0
    return score









