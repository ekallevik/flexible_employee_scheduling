from gurobipy import *
from xml_loader import xml_loader
from xml_loader.xml_loader import *
from utils import const
from collections import defaultdict



def get_time_steps(root):

    demands = get_demand_definitions(root)
    time_step_length = 1

    for demand in demands:
        for i in range(len(demand.end)):
            if demand.end[i] - int(demand.end[i]) > 0:
                if demand.end[i] - int(demand.end[i]) == 0.5 and time_step_length > 0.5:
                    time_step_length = 0.5
                elif demand.end[i] - int(demand.end[i]) in [0.25, 0.75] and time_step_length > 0.25:
                    time_step_length = 0.25
                elif demand.end[i] - int(demand.end[i]) < 0.25:
                    time_step_length = 1 / 60
                    break

            if demand.start[i] - int(demand.start[i]) > 0:
                if demand.start[i] - int(demand.start[i]) == 0.5 and time_step_length > 0.5:
                    time_step_length = 0.5
                elif (
                    demand.start[i] - int(demand.start[i]) == [0.25, 0.75]
                    and time_step_length > 0.25
                ):
                    time_step_length = 0.25
                elif demand.start[i] - int(demand.start[i]) < 0.25:
                    time_step_length = 1 / 60
                    break

    return time_step_length


def get_time_periods(root):

    time_periods = []
    time_step = get_time_steps(root)
    demands = get_days_with_demand(root)
    time_periods_in_week = tupledict()
    time_periods_in_day = defaultdict(list)
    week = 0
    day = 0
    time_periods_in_week[week] = tuplelist()

    for dem in demands:
        for i in range(len(demands[dem].start)):
            time = demands[dem].start[i] + 24 * dem
            end = demands[dem].end[i] + 24 * dem
            # Håndterer special cases hvor demand end er mindre enn demand start
            if end <= time:
                end += 24
            while time < end:
                if time > (week + 1) * 24 * 7:
                    week += 1
                    time_periods_in_week[week] = []
                if(time > (day+1)*24):
                    day += 1
                if time not in time_periods:
                    time_periods.append(time)
                    time_periods_in_week[week].append(time)
                    time_periods_in_day[day].append(time)
                time += time_step
    return [time_periods, time_periods_in_week, time_periods_in_day]

def get_demand(root, competencies):
    demand = {"min": tupledict(), "ideal": tupledict(), "max": tupledict()}

    time_step = get_time_steps(root)
    demands = get_days_with_demand(root)

    for c in competencies:
        for dem in demands:
            for i in range(len(demands[dem].start)):
                t = demands[dem].start[i] + 24 * dem
                while t < demands[dem].end[i] + 24 * dem:
                    try:
                        demand["min"][c, t] += demands[dem].minimum[i]
                    except:
                        demand["min"][c, t] = demands[dem].minimum[i]
                    try:
                        demand["ideal"][c, t] += demands[dem].ideal[i]
                    except:
                        demand["ideal"][c, t] = demands[dem].ideal[i]
                    try:
                        demand["max"][c, t] += demands[dem].maximum[i]
                    except:
                        demand["max"][c, t] = demands[dem].maximum[i]
                    t += time_step

    return demand


def get_events(root):

    events = []
    demand_days = get_days_with_demand(root)

    for day in demand_days:
        for t in range(len(demand_days[day].start)):
            if demand_days[day].end[t] == 0:
                demand_days[day].end[t] += 24
            if demand_days[day].start[t] + 24 * day not in events:
                events.append(demand_days[day].start[t] + 24 * day)
            if demand_days[day].end[t] - demand_days[day].start[t] >= 12:
                diff = (demand_days[day].end[t] - demand_days[day].start[t]) / 2
                if demand_days[day].start[t] + 24 * day + diff not in events:
                    events.append(demand_days[day].start[t] + 24 * day + diff)
            if demand_days[day].end[t] + 24 * day not in events:
                events.append((demand_days[day].end[t] + 24 * day))

    return events


def get_employee_lists(root, competencies):

    employees = tuplelist()
    employee_with_competencies = tupledict()
    employee_weekly_rest = tupledict()
    employee_daily_rest = tupledict()
    employee_contracted_hours = tupledict()
    employee_daily_offset = tupledict()

    emp = get_staff(root, competencies)

    for c in range(len(competencies)):
        employee_with_competencies[c] = []
        for e in emp:
            if c in e.competencies:
                employee_with_competencies[c].append(int(e.id))

    for e in emp:
        id = int(e.id)
        employees.append(id)
        employee_daily_rest[id] = e.daily_rest_hours
        employee_weekly_rest[id] = e.daily_rest_hours
        employee_contracted_hours[id] = e.contracted_hours
        employee_daily_offset[id] = e.daily_offset

    return {
        "employees": employees,
        "employees_with_competencies": employee_with_competencies,
        "employee_with_weekly_rest": employee_weekly_rest,
        "employee_daily_rest": employee_daily_rest,
        "employee_contracted_hours": employee_contracted_hours,
        "employee_daily_offset": employee_daily_offset,
    }


def get_demand_pairs(demand, day):
    """ Return a list of demand pair tuples in a day, representing the time intervals (TimeStart, TimeEnd) for demand
        rows in a DemandID """

    start_times = [t + 24 * int(day) for t in demand.start]
    end_times = [t + 24 * int(day) for t in demand.end]
    demand_pairs = []

    for i in range(len(start_times)):
        demand_pairs.append((start_times[i], end_times[i]))

    return demand_pairs


def get_day_demand_intervals(demand, day):
    """ Returns a list of related demand pairs. Demand pairs like (07:00, 10:00) and (10:00, 14:00) are merged to
        form the the related interval [07:00, 10:00, 14:00].  Unrelated demand pairs, like (07:00, 10:00) and
        (20:00, 24:00) are kept separate, forming [[07:00, 10:00],[20:00, 24:00]]"""

    demand_pairs = get_demand_pairs(demand, day)
    related_intervals = []

    if len(demand_pairs) == 1:
        related_intervals.append([demand_pairs[0][0], demand_pairs[0][1]])
    else:
        for index in range(len(demand_pairs)):
            temp_related_intervals = [demand_pairs[index][0], demand_pairs[index][1]]
            for pair in demand_pairs[index + 1 :]:
                if temp_related_intervals[-1] == pair[0]:
                    temp_related_intervals.append(pair[1])
                    demand_pairs.remove(pair)
                else:
                    break
            related_intervals.append(temp_related_intervals)
            if index is len(demand_pairs) - 1:
                break

    return related_intervals


def get_demand_intervals(root):
    """ Returns a dict, representing the day_demand_intervals for each day """

    daily_demand = get_days_with_demand(root)
    daily_demand_intervals = {}

    for day in daily_demand:
        daily_demand_intervals[day] = get_day_demand_intervals(daily_demand[day], day)

    return daily_demand_intervals


def combine_demand_intervals(root):
    """ Returns a complete list including all demand intervals and connecting all demand intervals that could be
        connected. The latter makes it possible to connect a 24-hour demand in one day to the 24-hour demand the
        next day. """

    demand_intervals = get_demand_intervals(root)
    interval_list = []
    combined_demand_intervals = []

    for day in demand_intervals:
        for interval in demand_intervals[day]:
            interval_list.append(interval)

    while len(interval_list) != 0:
        end_time = interval_list[0][-1]
        temp_interval = interval_list[0]
        for other_intervals in interval_list[1:]:
            if other_intervals[0] == end_time:
                for time in other_intervals[1:]:
                    temp_interval.append(time)
                interval_list.remove(other_intervals)
                break
        combined_demand_intervals.append(temp_interval)
        interval_list.pop(0)

    return combined_demand_intervals


def get_no_demand_intervals(demand_interval, day):
    """
    Returns a list of intervals during a day where there is no demand
    """

    end_time = 24 * (int(day) + 1)
    no_demand_intervals = []

    for intervals in demand_interval:
        start_time = intervals[0]
        if start_time > 24 * int(day) and intervals == demand_interval[0]:
            no_demand_intervals.append([24 * int(day), start_time])
        if start_time > end_time:
            overlapping_intervals = False
            for no_intervals in no_demand_intervals:
                if no_intervals[-1] > start_time:
                    overlapping_intervals = True
                    if no_demand_intervals[no_demand_intervals.index(no_intervals)][-1] > intervals[-1]:
                        no_demand_intervals[no_demand_intervals.index(no_intervals)][-1] = intervals[-1]
            if not overlapping_intervals:
                no_demand_intervals.append([end_time, start_time])
        end_time = intervals[-1]
    if end_time < 24 * (int(day) + 1):
        no_demand_intervals.append([end_time, 24 * (int(day) + 1)])

    return no_demand_intervals


def combine_no_demand_inetervals(root):
    """
    Returns a complete list including all intervals with no demand and connecting all demand intervals that could
    be connected.
    """

    demand_intervals = get_demand_intervals(root)
    interval_list = []
    combined_no_demand_intervals = []

    for day in demand_intervals:
        no_demand_intervals = get_no_demand_intervals(demand_intervals[day], day)
        for intervals in no_demand_intervals:
            interval_list.append(intervals)

    while len(interval_list) != 0:
        end_time = interval_list[0][-1]
        temp_interval = interval_list[0]
        for other_intervals in interval_list[1:]:
            if other_intervals[0] == end_time:
                for time in other_intervals[1:]:
                    temp_interval.append(time)
                interval_list.remove(other_intervals)
                break
        combined_no_demand_intervals.append([temp_interval[0], temp_interval[-1]])
        interval_list.pop(0)

    return combined_no_demand_intervals


def already_daily_off_shift(root, employee_offset, employee_rest, day):
    """
    Checks if an employee specific day has a interval without demand that exceeds the daily rest hours. If so,
    there is no need to ensure that daily rest is satisfied, as this is ensured naturally. Returns True or False.
    """

    no_demand_periods = combine_no_demand_inetervals(root)
    days = get_days(root)

    for interval in no_demand_periods:
        if day == len(days) - 1 and interval == no_demand_periods[-1] and interval[1] == 24 * len(days):
            temp_val = interval[1]
            interval[1] = temp_val + employee_offset
        if employee_offset + (24 * int(day)) <= interval[0] <= employee_offset + (24 * (int(day) + 1)):
            if interval[1] - interval[0] >= employee_rest:
                if interval[0] + employee_rest <= employee_offset + (24 * (int(day) +1)):
                    return True
        if interval[0] > employee_offset + (24 * (int(day) + 1)):
            break

    return False


def get_shift_lists(root):

    desired_dur = const.DESIRED_SHIFT_DURATION
    demand_intervals = combine_demand_intervals(root)
    shifts = tuplelist()

    for intervals in demand_intervals:
        if len(intervals) == 2:
            start_time = intervals[0]
            dur = intervals[1] - start_time
            if dur >= max(desired_dur):
                shifts.append((start_time, dur))
            else:
                shifts.append((start_time, intervals[1] - start_time))
        else:
            for time in intervals:
                found_shift = False
                for t in intervals[intervals.index(time) :]:
                    dur = t - time
                    if min(desired_dur) <= dur <= max(desired_dur):
                        shifts.append((time, dur))
                        found_shift = True
                    if dur > max(desired_dur) and not found_shift:
                        shifts.append((time, dur))

    shifts_per_day = tupledict()
    shifts_in_week = defaultdict(list)
    time_defining_shift_day = const.TIME_DEFINING_SHIFT_DAY

    for day in get_days(root):
        shifts_per_day[day] = []
        for shift in shifts:
            if (
                24 * (int(day) - 1) + time_defining_shift_day
                <= shift[0]
                < 24 * int(day) + time_defining_shift_day
            ):
                shifts_per_day[day].append(shift)
                shifts_in_week[int(day/7)].append(shift)
            if shift[0] >= 24 * int(day) + time_defining_shift_day:
                if day == get_days(root)[-1]:
                    shifts_per_day[day].append(shift)
                break

    return [shifts, shifts_per_day, shifts_in_week]


def get_shifts_violating_daily_rest(root, staff):
    """
    Returns to values:
        * violating_shifts: Returns a dict, with "employee" as key and another dict as value. The new dict uses "shift"
                            as key and have a list of shifts that violates daily rest for "employee" if "shift" is
                            worked.
        * invalid_shifts:   Returns a dict with "employee" as key and a list of shifts that is not allowed due to daily
                            rest as value.
    """

    employees = staff["employees"]
    daily_rest = staff["employee_daily_rest"]
    daily_offset = staff["employee_daily_offset"]
    daily_shifts = get_shift_lists(root)[1]
    violating_shifts = tupledict()
    invalid_shifts = tupledict()

    for e in employees:
        violating_shifts[e] = tupledict()
        invalid_shifts[e] = tuplelist()
        for day in daily_shifts:
            if not (already_daily_off_shift(root, daily_offset[e], daily_rest[e], day)):
                for shift in daily_shifts[day]:
                    if day != 0:
                        for s in daily_shifts[day - 1]:
                            if s[0] + s[1] > (24 * int(day)) + daily_offset[e]:
                                if shift[0] - (s[0] + s[1]) < daily_rest[e] and shift[0] >= (s[0] + s[1]):
                                    try:
                                        violating_shifts[e][shift].append(s)
                                    except:
                                        violating_shifts[e][shift] = [s]
                    if day != daily_shifts.keys()[-1]:
                        for s in daily_shifts[day + 1]:
                            if s[0] < 24 * (int(day) + 1) + daily_offset[e]:
                                if s[0] - (shift[0] + shift[1]) < daily_rest[e] and s[0] > (shift[0] + shift[1]):
                                    try:
                                        violating_shifts[e][shift].append(s)
                                    except:
                                        violating_shifts[e][shift] = [s]

                    if shift[0] - (24 * int(day)) - daily_offset[e] < daily_rest[e]:
                        if 24 * (int(day) + 1) + daily_offset[e] - (shift[0] + shift[1]) < daily_rest[e]:
                            try:
                                invalid_shifts[e].append(shift)
                            except:
                                invalid_shifts[e] = [shift]

    return [violating_shifts, invalid_shifts]


def get_shifts_overlapping_t(root):

    time_periods = get_time_periods(root)[0]
    shifts_overlapping_t = {}
    shifts = get_shift_lists(root)[0]

    for time in time_periods:
        for shift in shifts:
            if shift[0] <= time < shift[0] + shift[1]:
                try:
                    shifts_overlapping_t[time].append(shift)
                except:
                    shifts_overlapping_t[time] = [shift]

    return shifts_overlapping_t


def get_start_events(root):

    events = []
    demand_days = get_days_with_demand(root)

    for day in demand_days:
        for t in range(len(demand_days[day].start)):
            for j in range(len(demand_days[day].end)):
                diff = demand_days[day].end[j] - demand_days[day].start[t]
                if diff >= 6:
                    events.append((demand_days[day].start[t] + 24 * day))
                    break

    return events


def get_off_shifts(root):

    events = get_start_events(root)
    off_shifts = []
    off_shifts_in_week = tupledict()
    week = 0
    off_shifts_in_week[week] = []

    for i in range(len(events)):
        for event in events[i:]:
            dur = event - events[i]
            if events[i] >= (week + 1) * 24 * 7:
                week += 1
                off_shifts_in_week[week] = []
            if event >= (week + 1) * 24 * 7:
                break
            if dur > 70:
                break
            elif dur >= 36:
                if (events[i], dur) not in off_shifts:
                    off_shifts_in_week[week].append((events[i], dur))
                    off_shifts.append((events[i], dur))

    return [off_shifts, off_shifts_in_week]


def get_t_covered_by_off_shifts(root):

    off_shifts = get_off_shifts(root)[0]
    t_covered = tupledict()
    time_periods = get_time_periods(root)[0]

    for shift in off_shifts:
        end = time_periods.index(shift[0] + shift[1])
        start = time_periods.index(shift[0])
        t_covered[shift[0], shift[1]] = time_periods[start:end]

    return t_covered


def get_t_covered_by_shift(root):
    time_step = get_time_steps(root)
    shifts = get_shift_lists(root)[0]
    time_periods = get_time_periods(root)[0]
    t_covered_by_shift = tupledict()
    for shift in shifts:
        end = time_periods.index(shift[0] + shift[1] - time_step)
        start = time_periods.index(shift[0])
        t_covered_by_shift[shift[0], shift[1]] = time_periods[start:(end + 1)]
    return t_covered_by_shift

def shift_lookup(root):
    shifts = get_shift_lists(root)[1]
    shift_lookup = {}
    for key in shifts.keys():
        for value in shifts[key]:
            shift_lookup[value] = key
    return shift_lookup


def get_shifts_covered_by_off_shifts(root):

    off_shifts = get_off_shifts(root)[0]
    shifts_covered = tupledict()
    shifts = get_shift_lists(root)[0]

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

    competencies = get_competencies(root)
    shift_set = get_shift_lists(root)
    off_shift_set = get_off_shifts(root)
    days = get_days(root)
    number_of_weeks = int(len(days) / 7)
    weeks = [i for i in range(number_of_weeks)]
    saturdays = [5+i*7 for i in range(number_of_weeks)]
    sundays = [6+i*7 for i in range(number_of_weeks)]
    staff = get_employee_lists(root, competencies)

    data = {
        "competencies": competencies,
        "demand": get_demand(root, competencies),
        "staff": staff,
        "limit_on_consecutive_days": 5,
        "shifts": {
            "shifts_covered_by_off_shift": get_shifts_covered_by_off_shifts(root),
            "shifts_overlapping_t": get_shifts_overlapping_t(root),
            "shifts": shift_set[0],
            "shifts_per_day": shift_set[1],
            "shifts_in_week": shift_set[2],
            "shifts_combinations_violating_daily_rest": get_shifts_violating_daily_rest(root, staff)[0],
            "invalid_shifts_violating_daily_rest": get_shifts_violating_daily_rest(root, staff)[1],
        },
        "off_shifts": {
            "t_in_off_shifts": get_t_covered_by_off_shifts(root),
            "off_shifts": off_shift_set[0],
            "off_shifts_per_week": off_shift_set[1],
        },
        "time": {
            "step": get_time_steps(root),
            "periods": get_time_periods(root),
            "days": days,
            "weeks": weeks,
            "saturdays": saturdays,
            "sundays": sundays

        },
        "heuristic": {
            "t_covered_by_shift": get_t_covered_by_shift(root),
            "shift_lookup": shift_lookup(root),
        }
    }

    return data
