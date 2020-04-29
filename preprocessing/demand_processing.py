from collections import defaultdict

from gurobipy import *

from preprocessing.xml_loader import get_demand_definitions, get_days_with_demand


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
                if time > (day + 1) * 24:
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
                    if (
                        no_demand_intervals[no_demand_intervals.index(no_intervals)][-1]
                        > intervals[-1]
                    ):
                        no_demand_intervals[no_demand_intervals.index(no_intervals)][
                            -1
                        ] = intervals[-1]
            if not overlapping_intervals:
                no_demand_intervals.append([end_time, start_time])
        end_time = intervals[-1]
    if end_time < 24 * (int(day) + 1):
        no_demand_intervals.append([end_time, 24 * (int(day) + 1)])

    return no_demand_intervals


def combine_no_demand_intervals(root):
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
