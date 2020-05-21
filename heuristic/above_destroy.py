def reduce_overstaffing_with_destroy(state, shifts, employees, weeks, t_covered_by_shift,
                                   competencies,
                                   combined_time_periods_in_week, time_step, shifts_covering_t):
    destroy_set = []
    repair_set = []

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

    understaffed = {t: sum(state.hard_vars["below_minimum_demand"][c, t]
                          for c in competencies
                          if state.hard_vars["below_minimum_demand"].get((c, t)))
                   for j in weeks
                   for t in combined_time_periods_in_week[j]
                   if sum(state.hard_vars["below_minimum_demand"][c, t]
                          for c in competencies
                          if state.hard_vars["below_minimum_demand"].get((c, t))) > 0
                   }

    shifts_with_overstaffing = {shift
                                for t in overstaffed.keys()
                                for shift in shifts_covering_t[t]}

    shift_heap = []

    for shift in shifts_with_overstaffing:
        score = get_staffing_score_for_shift(overstaffed, shift, t_covered_by_shift, understaffed)

        # It is not beneficial to include shifts with more understaffing than overstaffing
        if score > -shift[1]:
            push_to_max_heap(shift_heap, score, shift)

    while shift_heap:

        estimated_score, shift = pop_from_max_heap(shift_heap)
        logger.trace(f"Looking into shift {shift}")

        actual_score = get_staffing_score_for_shift(overstaffed, shift, t_covered_by_shift, understaffed)

        if actual_score <= -shift[1]:
            logger.trace(f"Shift {shift} covers more understaffing than overstaffing")
            continue

        relevant_employees = [employee for employee in employees
                              if (employee, shift[0], shift[1]) in state.x]

        # todo: use this in a better way
        employee = relevant_employees[0]

        destroy_set.append(
            remove_x(state, t_covered_by_shift, competencies, employee,
                     shift[0], shift[1])
        )
        logger.info(f"Employee {employee} removed from shift {shift}")

        for t in t_covered_by_shift[shift]:

            if overstaffed.get(t, 0) > 1:
                overstaffed[t] -= 1
            elif overstaffed.get(t) == 1:
                del overstaffed[t]

            if understaffed.get(t, 0) > 1:
                understaffed[t] -= 1
            elif understaffed.get(t) == 1:
                del understaffed[t]

        updated_score = get_staffing_score_for_shift(overstaffed, shift, t_covered_by_shift,
                                                understaffed)

        if updated_score > -shift[1]:
            logger.trace(f"Shift {shift} still contains more overstaffing than understaffing")
            push_to_max_heap(shift_heap, updated_score, shift)

    return repair_set, destroy_set
