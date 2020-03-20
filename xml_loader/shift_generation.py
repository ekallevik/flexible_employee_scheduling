from gurobipy import *

from xml_loader import xml_loader
from xml_loader.xml_loader import *


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
    week = 0
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
                if time not in time_periods:
                    time_periods.append(time)
                    time_periods_in_week[week].append(time)
                time += time_step
    return [time_periods, time_periods_in_week]


def get_demand_periods(root, competencies):
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

    emp = get_employees(root, competencies)

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

    return {
        "employees": employees,
        "employees_with_competencies": employee_with_competencies,
        "employee_with_weekly_rest": employee_weekly_rest,
        "employee_daily_rest": employee_daily_rest,
        "employee_contracted_hours": employee_contracted_hours,
    }


def get_durations(root):

    events = get_events(root)
    durations = {}

    # Possible durations are between 6.0 hours and 12.0 hours
    possible_durations = [t / 4 for t in range(6 * 4, (12 * 4 + 1))]

    for t in events:
        for dur in possible_durations:
            if t + dur in events:
                try:
                    durations[t].append(dur)
                except:
                    durations[t] = [dur]
    return durations


def get_shift_lists(root):

    durations = get_durations(root)
    shifts_per_day = tupledict()
    shifts = tuplelist()
    days = get_days(root)
    time_step = get_time_steps(root)

    for d in days:
        shifts_per_day[d] = []
        for t in durations:
            if d * 24 <= t <= (24 * (d + 1) - time_step):
                for dur in durations[t]:
                    shifts_per_day[d].append((t, dur))
                    shifts.append((t, dur))
            if t > 24 * d:
                continue
    return [shifts, shifts_per_day]


def get_shift_list(root):
    shifts = tuplelist()
    dur = get_durations(root)
    i = 0
    for t in dur:
        for v in dur[t]:
            shifts.append(i)
            i += 1
    return shifts


def get_shifts_overlapping_t(root):

    time_periods = get_time_periods(root)[0]
    shifts_overlapping_t = {}
    shifts = get_durations(root)

    for t in time_periods:
        for time in shifts:
            for dur in shifts[time]:
                if time <= t < time + dur:
                    try:
                        shifts_overlapping_t[t].append((time, dur))
                    except:
                        shifts_overlapping_t[t] = [(time, dur)]
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
    saturdays = [5 + i * 7 for i in range(number_of_weeks)]

    data = {
        "competencies": competencies,
        "demand": get_demand_periods(root, competencies),
        "staff": get_employee_lists(root, competencies),
        "limit_on_consecutive_days": 5,
        "shifts": {
            "shifts_covered_by_off_shifts": get_shifts_covered_by_off_shifts(root),
            "shifts_overlapping_t": get_shifts_overlapping_t(root),
            "shifts": shift_set[0],
            "shifts_per_day": shift_set[1],
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
        },
    }

    return data
