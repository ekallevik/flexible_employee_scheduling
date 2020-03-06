import xml_loader.xml_loader as loader


def get_saturdays(days):
    return [w for w in range(int(len(days) / 7))]


def get_sets():

    # todo: modify xml_loader such that this step is not necessary.
    days = loader.get_days()

    off_shifts, off_shift_in_week = loader.get_off_shifts()

    (
        employees,
        employee_with_competencies,
        employee_weekly_rest,
        employee_daily_rest,
        contracted_hours,
    ) = loader.get_employee_lists()

    time_periods, time_periods_in_week = loader.get_time_periods()
    demand_min, demand_ideal, demand_max = loader.get_demand_periods()
    shifts, shifts_at_day = loader.get_shift_lists()

    return {
        "employees": {
            "all": employees,
            "competencies": employee_with_competencies,
            "employees_weekly_rest": employee_weekly_rest,
            "employees_daily_rest": employee_daily_rest,
            "contracted_hours": contracted_hours,
        },
        "time": {
            "periods": time_periods,
            "periods_in_week": time_periods_in_week,
            "step": loader.get_time_steps(),
            "t_in_off_shifts": loader.get_t_covered_by_off_shifts(),
            "saturdays": get_saturdays(days),
            "weeks": days * 7,
            "days": days
        },
        "demand": {
            "min": demand_min,
            "ideal": demand_ideal,
            "max": demand_max},
        "shifts": {
            "shifts": shifts,
            "day": shifts_at_day,
            "off_shifts": off_shifts,
            "off_shift_in_week": off_shift_in_week,
        },
        "competencies": [0],
        "limit_for_consecutive_days": 5
    }
