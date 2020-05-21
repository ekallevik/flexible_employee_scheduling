
for t in t_covered_by_shift[replacement_shift]:

    if t in understaffed.keys() and t not in current_understaffing.keys():
        # this will make understaffing worse
        delta_understaffing -= 1

    if t not in understaffed.keys() and t in current_understaffing.keys():
        # this will make understaffing better
        delta_understaffing += 1

    if t not in understaffed.keys() and t not in current_understaffing.keys():
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

    if t in overstaffed.keys() and t not in current_overstaffing.keys():
        # this will make overstaffing worse
        delta_overstaffing -= 1
    if t in current_overstaffing.keys():
        # this will make overstaffing better
        delta_understaffing += 1
    if t not in overstaffed.keys() and t not in current_overstaffing.keys():
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