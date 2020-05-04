from collections import defaultdict

from preprocessing import xml_loader
from preprocessing.demand_processing import (
    combine_demand_intervals,
    combine_no_demand_intervals,
    get_demand,
    get_start_events,
    get_time_periods,
    get_time_steps,
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


def load_data(problem_name):
    root = xml_loader.get_root(problem_name)

    competencies = get_competencies(root)
    staff = get_employee_lists(root, competencies)
    time_sets = get_time_sets(root)

    off_shift_sets = get_off_shift_sets(root, time_sets)
    shifts = get_shifts(root)
    shift_sets = get_shift_sets(root, staff, time_sets, shifts, off_shift_sets["off_shifts"])

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
            # todo: move this into 'time'? or 'shifts'?
            "t_covered_by_shift": get_t_covered_by_shift(shift_sets["shifts"], time_sets),
            # todo: move into 'shifts'?
            "shift_lookup": get_shift_lookup(shift_sets["shifts_per_day"]),
        },
    }

    return data


def get_time_sets(root):

    days = get_days(root)
    number_of_weeks = int(len(days) / 7)

    return {
        "step": get_time_steps(root),
        "periods": get_time_periods(root),
        "days": days,
        "weeks": [i for i in range(number_of_weeks)],
        "saturdays": [5 + i * 7 for i in range(number_of_weeks)],
        "sundays": [6 + i * 7 for i in range(number_of_weeks)],
    }


def get_shift_sets(root, staff, time_sets, shifts, off_shifts):

    shifts_per_day, shifts_per_week = get_shifts_per_day(shifts, time_sets["days"])
    long_shifts, short_shifts = get_short_and_long_shifts(shifts)

    shifts_violating_daily_rest = get_shifts_violating_daily_rest(root, staff, shifts_per_day)
    invalid_shifts = get_invalid_shifts(root, staff, shifts_per_day)

    return {
        "shifts": shifts,
        "shifts_per_day": shifts_per_day,
        "shifts_per_week": shifts_per_week,
        "short_shifts": short_shifts,
        "long_shifts": long_shifts,
        "shifts_overlapping_t": get_shifts_overlapping_t(shifts, time_sets),
        "shifts_covered_by_off_shift": get_shifts_covered_by_off_shifts(shifts, off_shifts),
        "shift_sequences_violating_daily_rest": shifts_violating_daily_rest[0],
        "shift_combinations_violating_daily_rest": shifts_violating_daily_rest[1],
        "invalid_shifts": invalid_shifts,
    }


def get_updated_shift_sets(problem_name, data, shifts):

    root = xml_loader.get_root(problem_name)

    return get_shift_sets(
        root, data["staff"], data["time"], shifts, data["off_shifts"]["off_shifts"]
    )


def get_shifts(root):
    demand_intervals = combine_demand_intervals(root)
    shifts = tuplelist()

    for intervals in demand_intervals:

        if len(intervals) == 2:
            start_time = intervals[0]
            duration = intervals[1] - start_time

            if duration >= ALLOWED_SHIFT_DURATION[1]:
                shifts = get_shifts_for_long_duration(root, shifts, start_time, duration)
            else:
                shifts.append((start_time, intervals[1] - start_time))

        else:

            for time in intervals:
                found_shift = False

                for t in intervals[intervals.index(time):]:
                    duration = t - time
                    if ALLOWED_SHIFT_DURATION[0] <= duration <= ALLOWED_SHIFT_DURATION[1]:
                        shifts.append((time, duration))
                        found_shift = True
                    if 24 >= duration > ALLOWED_SHIFT_DURATION[1] and not found_shift:
                        shifts = get_shifts_for_long_duration(root, shifts, time, duration)

    shifts = remove_duplicates_and_sort(shifts)

    return shifts


def get_shifts_for_long_duration(root, shifts, time, duration):
    """
    Create shifts for long demand periods without change in demand. Makes two shifts that together cover the
    demand period. If possible, three additionally shifts are created that also together cover the demand period.
    """

    time_step = get_time_steps(root)

    # Create two base shifts
    half_duration = duration / 2

    if half_duration % time_step == 0:
        shifts.append((time, half_duration))
        shifts.append((time + half_duration, half_duration))
    else:
        allowed_half_duration = int(half_duration)
        while allowed_half_duration < half_duration:
            allowed_half_duration += time_step
        remaining_half_duration = duration - allowed_half_duration
        shifts.append((time, allowed_half_duration))
        shifts.append((time + allowed_half_duration, remaining_half_duration))

    # If possible, create three additionally shifts that covers the duration
    third_duration = duration / 3

    if third_duration > ALLOWED_SHIFT_DURATION[0]:
        if third_duration % time_step == 0:
            for i in range(3):
                shifts.append((time + (i * third_duration), third_duration))
        else:
            allowed_third_duration = int(third_duration)
            while allowed_third_duration < third_duration:
                allowed_third_duration += time_step
            remaining_third_duration = duration - (2 * allowed_third_duration)
            shifts.append((time, allowed_third_duration))
            shifts.append((time + allowed_third_duration, allowed_third_duration))
            shifts.append((time + (2 * allowed_third_duration), remaining_third_duration))

    return shifts


def remove_duplicates_and_sort(shifts):
    """ Remove duplicate shifts and sort them by starting time and then by duration """

    shifts = tuplelist(set(shifts))
    shifts.sort(key=lambda tup: (tup[0], tup[1]))

    return shifts


def get_shifts_per_day(shifts, days):

    # todo: bruke defaultdict for begge?
    shifts_per_day = tupledict()
    shifts_in_week = defaultdict(list)

    for day in days:
        shifts_per_day[day] = []

        for shift in shifts:

            if (
                24 * (int(day) - 1) + TIME_DEFINING_SHIFT_DAY
                <= shift[0]
                < 24 * int(day) + TIME_DEFINING_SHIFT_DAY
            ):
                shifts_per_day[day].append(shift)
                shifts_in_week[int(day / 7)].append(shift)

            if shift[0] >= 24 * int(day) + TIME_DEFINING_SHIFT_DAY:
                if day == days[-1]:
                    shifts_per_day[day].append(shift)
                break

    return shifts_per_day

    return shifts_per_day, shifts_in_week


def get_short_and_long_shifts(shifts):
    short_shifts = tuplelist()
    long_shifts = tuplelist()

    for s in shifts:
        if s[1] < DESIRED_SHIFT_DURATION[0]:
            short_shifts.append(s)
        elif s[1] > DESIRED_SHIFT_DURATION[1]:
            long_shifts.append(s)
    return long_shifts, short_shifts


def get_shifts_overlapping_t(shifts, time_sets):
    time_periods = time_sets["periods"][0]
    shifts_overlapping_t = {}

    for time in time_periods:
        for shift in shifts:
            if shift[0] <= time < shift[0] + shift[1]:
                try:
                    shifts_overlapping_t[time].append(shift)
                except:
                    shifts_overlapping_t[time] = [shift]

    return shifts_overlapping_t


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


def get_shifts_violating_daily_rest(root, staff, shifts_per_day):
    """
    Returns:
        * violating_shift_sequences:    A dict, with "employee" as key and another dict as value. The new dict
                                        uses "shift" as key, with value: a list of shifts sequences that, if two or
                                        more of them are worked, contributes to violating daily rest for "employee"
                                        if "shift" is worked.
        * violating_shift_combinations: A dict, with "employee" as key and another dict as value. The new dict uses
                                        "shift" as key, with value: a list of shifts that violates daily rest for
                                        "employee" if "shift" is worked.
    """

    employees = staff["employees"]
    daily_rest = staff["employee_daily_rest"]
    daily_offset = staff["employee_daily_offset"]
    violating_shift_sequences = tupledict()
    violating_shift_combinations = tupledict()

    for e in employees:
        violating_shift_sequences[e] = tupledict()
        violating_shift_combinations[e] = tupledict()
        for day in shifts_per_day:
            # Check if daily rest is fulfilled naturally
            if not (already_daily_off_shift(root, daily_offset[e], daily_rest[e], day)):
                for shift in shifts_per_day[day]:
                    if day != 0:
                        # Checking shifts the day before
                        for s in shifts_per_day[day - 1]:
                            # Checking if the shift from the day before is ending in employee specific day
                            if s[0] + s[1] > (24 * int(day)) + daily_offset[e]:
                                # Checking if daily rest occurs between the shifts and that they are not overlapping
                                if shift[0] - (s[0] + s[1]) < daily_rest[e] and shift[0] >= (s[0] + s[1]):
                                    try:
                                        violating_shift_sequences[e][shift].append(s)
                                    except:
                                        violating_shift_sequences[e][shift] = [s]

                                    # Check if shift combination forces violation of daily rest
                                    if 24 * (int(day) + 1) + daily_offset[e] - (shift[0] + shift[1]) < daily_rest[e]:
                                        try:
                                            violating_shift_combinations[e][shift].append(s)
                                        except:
                                            violating_shift_combinations[e][shift] = [s]

                    if day != shifts_per_day.keys()[-1]:
                        # Checking shifts the next day
                        for s in shifts_per_day[day + 1]:
                            # Checking if the shift in the next day is starting within employee specific dat
                            if s[0] < 24 * (int(day) + 1) + daily_offset[e]:
                                # Checking if daily rest occurs between the shifts and that they are not overlapping
                                if s[0] - (shift[0] + shift[1]) < daily_rest[e] and s[0] > (shift[0] + shift[1]):
                                    try:
                                        violating_shift_sequences[e][shift].append(s)
                                    except:
                                        # If there are no violating shifts from day before, nothing should be done
                                        pass

                                    # Check if shift combination forces violation of daily rest
                                    if shift[0] - (24 * int(day) + daily_offset[e]) < daily_rest[e]:
                                        try:
                                            violating_shift_combinations[e][shift].append(s)
                                        except:
                                            violating_shift_combinations[e][shift] = [s]

        # Removing violating shift sequences that only consists of either shifts on day before or next day
        for shift in violating_shift_sequences[e].keys():
            shifts_from_day_before, shifts_from_next_day = False, False
            for s in violating_shift_sequences[e][shift]:
                if s[0] < shift[0]:
                    shifts_from_day_before = True
                elif s[0] > shift[0] + shift[1]:
                    shifts_from_next_day = True
            if not shifts_from_day_before or not shifts_from_next_day:
                del violating_shift_sequences[e][shift]

    return [violating_shift_sequences, violating_shift_combinations]


def get_invalid_shifts(root, staff, shifts_per_day):
    """
    Returns a dict with employee as key, and all shifts that are invalid either due to blocked
    hours or daily rest as value.
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
                if not natural_rest:
                    if shift[0] - (24 * int(day)) - daily_offset[e] < daily_rest[e]:
                        if (
                            24 * (int(day) + 1) + daily_offset[e] - (shift[0] + shift[1])
                            < daily_rest[e]
                        ):
                            if not shift_used:
                                invalid_shifts[e].append(shift)

    return invalid_shifts


def get_t_covered_by_shift(shifts, time_sets):

    time_step = time_sets["step"]
    time_periods = time_sets["periods"][0]
    t_covered_by_shift = tupledict()

    for shift in shifts:
        end = time_periods.index(shift[0] + shift[1] - time_step)
        start = time_periods.index(shift[0])
        t_covered_by_shift[shift[0], shift[1]] = time_periods[start : (end + 1)]

    return t_covered_by_shift


def get_shift_lookup(shifts_per_day):

    shift_lookup = {}

    for key in shifts_per_day.keys():
        for value in shifts_per_day[key]:
            shift_lookup[value] = key

    return shift_lookup


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
            24 * int(day)
            <= interval[0]
            <= employee_offset + (24 * (int(day) + 1))
        ):
            if interval[1] - interval[0] - max(employee_offset - interval[0], 0) >= employee_rest:
                if interval[0] + employee_rest <= employee_offset + (24 * (int(day) + 1)):
                    return True
        if interval[0] > employee_offset + (24 * (int(day) + 1)):
            break

    return False


def get_off_shift_sets(root, time_sets):

    off_shift_set = get_off_shifts(root)

    return {
        "t_in_off_shifts": get_t_covered_by_off_shifts(off_shift_set[0], time_sets),
        "off_shifts": off_shift_set[0],
        "off_shifts_per_week": off_shift_set[1],
    }


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


def get_t_covered_by_off_shifts(off_shifts, time_sets):

    t_covered = tupledict()
    time_periods = time_sets["periods"][0]

    for shift in off_shifts:
        end = time_periods.index(shift[0] + shift[1])
        start = time_periods.index(shift[0])
        t_covered[shift[0], shift[1]] = time_periods[start:end]

    return t_covered
