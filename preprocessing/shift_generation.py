from preprocessing import xml_loader
from preprocessing.demand_processing import (
    combine_demand_intervals,
    combine_no_demand_intervals,
    get_demand,
    get_start_events,
    get_time_periods,
    get_time_steps,
    get_combined_time_periods,
)
from preprocessing.preferences import generate_preferences
from preprocessing.xml_loader import *
from utils.const import (
    ALLOWED_SHIFT_DURATION,
    DESIRED_SHIFT_DURATION,
    DURATION_OF_PREFERENCES,
    NUMBER_OF_PREFERENCES_PER_WEEK,
    TIME_DEFINING_SHIFT_DAY,
)


def already_daily_off_shift(root, employee_offset, employee_rest, day):
    """
    Checks if an employee specific day has a interval without demand that exceeds the daily rest
    hours. If so, there is no need to ensure that daily rest is satisfied, as this is ensured
    naturally. Returns True or False.
    """

    no_demand_intervals = combine_no_demand_intervals(root)
    days = get_days(root)

    for interval in no_demand_intervals:
        if (
            day == len(days) - 1
            and interval == no_demand_intervals[-1]
            and interval[1] == 24 * len(days)
        ):
            temp_val = interval[1]
            interval[1] = temp_val + employee_offset
        if (
            employee_offset + (24 * int(day))
            <= interval[0]
            <= employee_offset + (24 * (int(day) + 1))
        ):
            if interval[1] - interval[0] >= employee_rest:
                if interval[0] + employee_rest <= employee_offset + (24 * (int(day) + 1)):
                    return True
        if interval[0] > employee_offset + (24 * (int(day) + 1)):
            break

    return False


def get_shifts(root):

    demand_intervals = combine_demand_intervals(root)
    shifts = tuplelist()

    for intervals in demand_intervals:

        if len(intervals) == 2:
            start_time = intervals[0]
            duration = intervals[1] - start_time

            if duration >= ALLOWED_SHIFT_DURATION[1]:
                if((start_time, duration) not in shifts):
                    shifts.append((start_time, duration))
            else:
                if((start_time, intervals[1] - start_time) not in shifts):
                    shifts.append((start_time, intervals[1] - start_time))

        else:

            for time in intervals:
                found_shift = False

                for t in intervals[intervals.index(time) :]:
                    duration = t - time
                    if ALLOWED_SHIFT_DURATION[0] <= duration <= ALLOWED_SHIFT_DURATION[1]:
                        if((time, duration) not in shifts):
                            shifts.append((time, duration))
                            found_shift = True
                    if duration > ALLOWED_SHIFT_DURATION[1] and not found_shift:
                        shifts.append((time, duration))
    return shifts


def get_short_and_long_shifts(shifts):

    short_shifts = tuplelist()
    long_shifts = tuplelist()

    for s in shifts:
        if s[1] < DESIRED_SHIFT_DURATION[0]:
            short_shifts.append(s)
        elif s[1] > DESIRED_SHIFT_DURATION[1]:
            long_shifts.append(s)
    return long_shifts, short_shifts


def get_shifts_per_day(shifts, days):

    shifts_per_day = tupledict()

    for day in days:
        shifts_per_day[day] = []

        for shift in shifts:

            if (
                24 * (int(day) - 1) + TIME_DEFINING_SHIFT_DAY
                <= shift[0]
                < 24 * int(day) + TIME_DEFINING_SHIFT_DAY
            ):
                shifts_per_day[day].append(shift)

            if shift[0] >= 24 * int(day) + TIME_DEFINING_SHIFT_DAY:
                if day == days[-1]:
                    shifts_per_day[day].append(shift)
                break
    return shifts_per_day


def get_shifts_violating_daily_rest(root, staff, shifts_per_day):
    """
    Returns:
        * violating_shifts:     Returns a dict, with "employee" as key and another dict as value. The
                                new dict uses "shift" as key and have a list of shifts that violates daily rest for
                                "employee" if "shift" is worked.
    """

    employees = staff["employees"]
    daily_rest = staff["employee_daily_rest"]
    daily_offset = staff["employee_daily_offset"]
    violating_shifts = tupledict()

    for e in employees:
        violating_shifts[e] = tupledict()
        for day in shifts_per_day:
            if not (already_daily_off_shift(root, daily_offset[e], daily_rest[e], day)):
                for shift in shifts_per_day[day]:
                    if day != 0:
                        for s in shifts_per_day[day - 1]:
                            if s[0] + s[1] > (24 * int(day)) + daily_offset[e]:
                                if shift[0] - (s[0] + s[1]) < daily_rest[e] and shift[0] >= (
                                    s[0] + s[1]
                                ):
                                    try:
                                        violating_shifts[e][shift].append(s)
                                    except:
                                        violating_shifts[e][shift] = [s]
                    if day != shifts_per_day.keys()[-1]:
                        for s in shifts_per_day[day + 1]:
                            if s[0] < 24 * (int(day) + 1) + daily_offset[e]:
                                if s[0] - (shift[0] + shift[1]) < daily_rest[e] and s[0] > (
                                    shift[0] + shift[1]
                                ):
                                    try:
                                        violating_shifts[e][shift].append(s)
                                    except:
                                        violating_shifts[e][shift] = [s]

    return violating_shifts


def get_invalid_shifts(root, staff, shifts_per_day):
    """
    Returns:
        * invalid_shifts:   Dict with employee as key, and all shifts that are invalid either due to blocked hours or
                            daily rest as value.
    """

    employees = staff["employees"]
    daily_rest = staff["employee_daily_rest"]
    daily_offset = staff["employee_daily_offset"]
    blocked_hours = staff["employee_blocked_hours"]
    invalid_shifts = tupledict()

    for e in employees:
        invalid_shifts[e] = tuplelist()
        for day in shifts_per_day:
            natural_rest = already_daily_off_shift(root, daily_offset[e], daily_rest[e], day)
            for shift in shifts_per_day[day]:
                shift_used = False
                # BLOCKED HOURS
                for time in blocked_hours[e]:
                    if shift[0] <= time < shift[0] + shift[1]:
                        invalid_shifts[e].append(shift)
                        shift_used = True
                # INVALID SHIFTS DUE TO DAILY REST
                if not (natural_rest):
                    if shift[0] - (24 * int(day)) - daily_offset[e] < daily_rest[e]:
                        if (
                            24 * (int(day) + 1) + daily_offset[e] - (shift[0] + shift[1])
                            < daily_rest[e]
                        ):
                            if not (shift_used):
                                invalid_shifts[e].append(shift)

    return invalid_shifts


def get_shifts_overlapping_t(shifts, time_sets, competencies):

    time_periods = time_sets["periods"][0]
    shifts_overlapping_t = {}

    for c in competencies:
        for time in time_periods[c]:
            for shift in shifts:
                if shift[0] <= time < shift[0] + shift[1]:
                    try:
                        if(shift not in shifts_overlapping_t[time]):
                            shifts_overlapping_t[time].append(shift)
                    except:
                        shifts_overlapping_t[time] = [shift]
    return shifts_overlapping_t


def get_off_shifts(root):

    events = get_start_events(root)

    off_shifts = []
    off_shifts_in_week = tupledict()
    week = 0
    off_shifts_in_week[week] = []

    for i in range(len(events)):
        for event in events[i:]:
            duration = event - events[i]
            if events[i] >= (week + 1) * 24 * 7:
                week += 1
                off_shifts_in_week[week] = []
            if event >= (week + 1) * 24 * 7:
                break
            if duration > 70:
                break
            elif duration >= 36:
                if (events[i], duration) not in off_shifts:
                    off_shifts_in_week[week].append((events[i], duration))
                    off_shifts.append((events[i], duration))

    return [off_shifts, off_shifts_in_week]


def get_t_covered_by_off_shifts(off_shifts, time_sets, competencies):
    t_covered = tupledict()
    time_periods = time_sets["periods"][0]
    for shift in off_shifts:
        for c in competencies: 
            try:
                end = time_periods[c].index(shift[0] + shift[1])
                start = time_periods[c].index(shift[0])
                t_covered[shift[0], shift[1], c] = time_periods[c][start:end]
            except:  
                test = list(filter(lambda i: i >= shift[0] and i <= (shift[0] + shift[1]), time_periods[c]))
                if(len(test) == 0):
                    continue
                t_covered[shift[0], shift[1], c] = test

            
    return t_covered


def get_t_covered_by_shift(shifts, time_sets):

    time_step = time_sets["step"]
    time_periods = time_sets["periods"][0]
    t_covered_by_shift = tupledict()
    c = 0
    for shift in shifts:
        end = time_periods[c].index(shift[0] + shift[1] - time_step)
        start = time_periods[c].index(shift[0])
        t_covered_by_shift[shift[0], shift[1]] = time_periods[c][start : (end + 1)]

    return t_covered_by_shift


def get_shift_lookup(shifts_per_day):

    shift_lookup = {}

    for key in shifts_per_day.keys():
        for value in shifts_per_day[key]:
            shift_lookup[value] = key

    return shift_lookup


def get_shifts_covered_by_off_shifts(shifts, off_shifts):

    shifts_covered = tupledict()

    for off_shift in off_shifts:
        shifts_covered[off_shift] = []
        for shift in shifts:
            if off_shift[0] <= shift[0] < (off_shift[0] + off_shift[1]) or off_shift[0] <= (
                shift[0] + shift[1]
            ) < (off_shift[0] + off_shift[1]):
                shifts_covered[off_shift].append(shift)

    return shifts_covered


def load_data(problem_name):
    root = xml_loader.get_root(problem_name)

    competencies = []
    #Do not think we will use this anymore
    #competencies = get_competencies(root)
    
    staff = get_employee_lists(root, competencies)
    time_sets = get_time_sets(root, competencies)

    off_shift_sets = get_off_shift_sets(root, time_sets, competencies)

    shifts = get_shifts(root)

    shift_sets = get_shift_sets(root, staff, time_sets, shifts, off_shift_sets["off_shifts"], competencies)

    data = {
        "competencies": competencies,
        "demand": get_demand(root, competencies),
        "staff": staff,
        "limit_on_consecutive_days": 5,
        "preferences": generate_preferences(
            staff, time_sets, NUMBER_OF_PREFERENCES_PER_WEEK, DURATION_OF_PREFERENCES
        ),
        "shifts": shift_sets,
        "off_shifts": off_shift_sets,
        "time": time_sets,
        "heuristic": {
            "t_covered_by_shift": get_t_covered_by_shift(shift_sets["shifts"], time_sets),
            "shift_lookup": get_shift_lookup(shift_sets["shifts_per_day"]),
        },
    }

    return data


def get_time_sets(root, competencies):

    days = get_days(root)
    number_of_weeks = int(len(days) / 7)
    periods = get_time_periods(root, competencies)
    return {
        "step": get_time_steps(root),
        "periods": periods,
        "combined_time_periods": get_combined_time_periods(periods[0], periods[1], periods[2]),
        "days": days,
        "weeks": [i for i in range(number_of_weeks)],
        "saturdays": [5 + i * 7 for i in range(number_of_weeks)],
        "sundays": [6 + i * 7 for i in range(number_of_weeks)],
    }


def get_off_shift_sets(root, time_sets, competencies):

    off_shift_set = get_off_shifts(root)

    return {
        "t_in_off_shifts": get_t_covered_by_off_shifts(off_shift_set[0], time_sets, competencies),
        "off_shifts": off_shift_set[0],
        "off_shifts_per_week": off_shift_set[1],
    }


def get_shift_sets(root, staff, time_sets, shifts, off_shifts, competencies):

    shifts_per_day = get_shifts_per_day(shifts, time_sets["days"])
    long_shifts, short_shifts = get_short_and_long_shifts(shifts)
    shifts_violating_daily_rest = get_shifts_violating_daily_rest(root, staff, shifts_per_day)
    invalid_shifts = get_invalid_shifts(root, staff, shifts_per_day)

    return {
        "shifts": shifts,
        "shifts_per_day": shifts_per_day,
        "short_shifts": short_shifts,
        "long_shifts": long_shifts,
        "shifts_overlapping_t": get_shifts_overlapping_t(shifts, time_sets, competencies),
        "shifts_covered_by_off_shift": get_shifts_covered_by_off_shifts(shifts, off_shifts),
        "shifts_combinations_violating_daily_rest": shifts_violating_daily_rest,
        "invalid_shifts": invalid_shifts,
    }


def get_updated_shift_sets(problem_name, data, shifts, competencies):

    root = xml_loader.get_root(problem_name)

    return get_shift_sets(
        root, data["staff"], data["time"], shifts, data["off_shifts"]["off_shifts"], competencies
    )
