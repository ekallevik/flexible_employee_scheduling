from gurobipy import *
from xml_loader import xml_loader
from xml_loader.xml_loader import *
from utils import const


def get_demand_pairs(demand, day):

    start_times = [t + 24 * int(day) for t in demand.start]
    end_times = [t + 24 * int(day) for t in demand.end]
    demand_pairs = []

    for i in range(len(start_times)):
        demand_pairs.append((start_times[i], end_times[i]))

    return demand_pairs


def get_demand_intervals(demand, day):

    demand_pairs = get_demand_pairs(demand, day)
    related_intervals = []

    if len(demand_pairs) == 1:
       related_intervals.append([demand_pairs[0][0], demand_pairs[0][1]])
    else:
        for index in range(len(demand_pairs)):
            temp_related_intervals = [demand_pairs[index][0], demand_pairs[index][1]]
            for pair in demand_pairs[index + 1:]:
                if temp_related_intervals[-1] == pair[0]:
                    temp_related_intervals.append(pair[1])
                    demand_pairs.remove(pair)
                else:
                    break
            related_intervals.append(temp_related_intervals)
            if index is len(demand_pairs) - 1:
                break
    return related_intervals


def get_daily_demand_intervals(root):

    daily_demand = get_days_with_demand(root)
    daily_demand_intervals = {}

    for day in daily_demand:
        daily_demand_intervals[day] = get_demand_intervals(daily_demand[day], day)

    return(daily_demand_intervals)


def combine_demand_intervals(root):

    daily_demand_intervals = get_daily_demand_intervals(root)
    interval_list = []
    combined_demand_intervals = []

    for day in daily_demand_intervals:
        for interval in daily_demand_intervals[day]:
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


def get_shift_lists(root):

    desired_dur = const.DESIRED_SHIFT_DURATION
    demand_intervals = combine_demand_intervals(root)
    shifts = tuplelist()

    for intervals in demand_intervals:
        if len(intervals) == 2:
            start_time = intervals[0]
            dur = intervals[1] - start_time
            if dur >= max(desired_dur):
                # Todo: handle long shifts
                shifts.append((time, dur))
            else:
                shifts.append((start_time, intervals[1] - start_time))
        else:
            for time in intervals:
                found_shift = False
                for t in intervals[intervals.index(time):]:
                    dur = t - time
                    if min(desired_dur) <= dur <= max(desired_dur):
                        shifts.append((time, dur))
                        found_shift = True
                    if dur > max(desired_dur) and not found_shift:
                        # Todo: handle long shifts
                        shifts.append((time, dur))

    shifts_per_day = tupledict()
    time_defining_shift_day = const.TIME_DEFINING_SHIFT_DAY
    for day in get_days(root):
        shifts_per_day[day] = []
        for shift in shifts:
            if 24 * (int(day) - 1) + time_defining_shift_day <= shift[0] < 24 * int(day) + time_defining_shift_day:
                shifts_per_day[day].append(shift)
            if shift[0] >= 24 * int(day) + time_defining_shift_day:
                if day == get_days(root)[-1]:
                    shifts_per_day[day].append(shift)
                break

    return [shifts, shifts_per_day]

