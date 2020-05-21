
def reduce_overstaffing_with_swaps(state, shifts, employees, weeks, t_covered_by_shift, competencies,
                                   combined_time_periods_in_week, time_step, shifts_covering_t):
    destroy_set = []
    repair_set = []

    logger.warning(f"Reducing overstaffing from current level: "
                   f"{sum(state.hard_vars['above_maximum_demand'].values())}")
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

        if not excess:
            # if the violation has been fixed in a previous iteration
            logger.info("The excess ")
            continue

        logger.info(f"Fix overstaffing for t={t}, excess={excess}")

        current_offset = time_step
        chosen_shift = None
        related_excess = {}
        impossible_shifts = set(shifts_covering_t[t])

        # note: this can contain impossible sets
        potential_shifts = set()

        # todo: maybe improve this?
        while current_offset <= 1:

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

        max_shift_score = 0
        chosen_shift = None

        if possible_shifts:
            logger.trace(f"Possible shifts for t in [{t-current_offset}, {t+current_offset}]")
            print()
            pprint(possible_shifts)
            print("\n\n")

            for shift in possible_shifts:
                time_periods = t_covered_by_shift[shift]
                shift_score = sum(min(excess, overstaffed.get(t, 0)) for t in time_periods)

                if shift_score >= max_shift_score:
                    max_shift_score = shift_score
                    chosen_shift = shift

        logger.info(f"Chosen shift {chosen_shift} removes {max_shift_score} excess")

        # todo: fix this
        if not chosen_shift:
            break

        #breakpoint()

        employee_taboo = []

        for _ in range(int(excess)):

            logger.info(f"Looking for {excess} employees")

            #breakpoint()

            if not shifts_covering_t[t]:
                logger.info("How is this possible??")
                breakpoint()

            # todo: use a regret-approach / estimation-approach? or sort?
            most_overworked_employee = None
            shift_to_remove = None
            largest_violation_of_contracted = 0

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

    logger.warning(f"Reduced overstaffing to updated level: "
                   f"{sum(state.hard_vars['above_maximum_demand'].values())}")

    return destroy_set, repair_set

