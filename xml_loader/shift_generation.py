import sys
from pathlib import Path
loader_path = str(Path(__file__).resolve().parent)
sys.path.insert(1, loader_path)
from gurobipy import *
from loader_2 import *
import xml.etree.ElementTree as ET

def get_time_steps(root):
    demands = get_demand_definitions(root)
    time_step_length = 100
    for demand in demands:
        for i in range(len(demand.end)):
            if(demand.end[i] - int(demand.end[i]) > 0):
                if(demand.end[i] - int(demand.end[i]) == 0.5 and time_step_length != 0.5):
                    time_step_length = 0.5
                elif(demand.end[i] - int(demand.end[i]) in [0.25,0.75] and time_step_length != 0.25):
                    time_step_length = 0.25
                elif(demand.end[i] - int(demand.end[i]) < 0.25):
                    time_step_length = 100/60
                    break
            if(demand.start[i] - int(demand.start[i]) > 0):
                if(demand.start[i] - int(demand.start[i]) == 0.5 and time_step_length < 0.5):
                    time_step_length = 0.5
                elif(demand.start[i] - int(demand.start[i]) == [0.25,0.75] and time_step_length < 0.25):
                    time_step_length = 0.25
                elif(demand.start[i] - int(demand.start[i]) < 0.25):
                    time_step_length = 100/60
                    break
    return time_step_length


def get_time_periods(root):
    time_periods = []
    i = 0
    time_step = get_time_steps(root)
    demands = get_days_with_demand(root)
    time_periods_in_week = tupledict()
    week = 0
    time_periods_in_week[week] = []
    for dem in demands:
        for i in range(len(demands[dem].start)):
            time = demands[dem].start[i] + 24*(dem)
            while(time < demands[dem].end[i] + 24*dem):
                if(time > (week+1)*24*7):
                    week += 1
                    time_periods_in_week[week] = []
                if(time not in time_periods):
                    time_periods.append(time)
                    time_periods_in_week[week].append(time)
                time += time_step
    return time_periods, time_periods_in_week


def get_demand_periods(root):
    min_demand = tupledict()
    ideal_demand = tupledict()
    max_demand = tupledict()
    competencies = [0]
    time_step = get_time_steps(root)
    demands = get_days_with_demand(root)
    for c in competencies:
        for dem in demands:
            for i in range(len(demands[dem].start)):
                t = demands[dem].start[i] + 24*(dem)
                while(t < demands[dem].end[i] + 24*dem):
                    try:
                        min_demand[c,t] += demands[dem].minimum[i]
                    except:
                        min_demand[c,t] = demands[dem].minimum[i]
                    try:
                        ideal_demand[c,t] += demands[dem].ideal[i]
                    except:
                        ideal_demand[c,t] = demands[dem].ideal[i]
                    try:
                        max_demand[c,t] += demands[dem].maks[i]
                    except:
                        max_demand[c,t] = demands[dem].maks[i]
                    t += time_step

    return min_demand, ideal_demand, max_demand


def get_events(root):
    events = []
    demand_days = get_days_with_demand(root)
    for day in demand_days:
        for t in range(len(demand_days[day].start)):
            if(demand_days[day].end[t] - demand_days[day].start[t] >= 12):
                diff = (demand_days[day].end[t] - demand_days[day].start[t])/2
                events.append(demand_days[day].start[t] + 24*day + diff)
            if(demand_days[day].start[t] + 24*day not in events):
                events.append(demand_days[day].start[t] + 24*day)
            if(demand_days[day].end[t] + 24*day not in events):
                events.append((demand_days[day].end[t] + 24*day))

    return events


def get_employee_lists(root):
    competencies = get_competencies(root)
    employee_with_competencies = tupledict()
    employees = tuplelist()
    employee_weekly_rest = tupledict()
    employee_daily_rest = tupledict()
    employee_contracted_hours = tupledict()
    emp = get_employees(root, competencies)
    if(len(competencies) == 0):
        competencies.append(0)
    for c in range(len(competencies)):
        employee_with_competencies[c] = []
        for e in emp:
            if(c in e.competencies):
                employee_with_competencies[c].append(int(e.id))
    
    for e in emp:
        id = int(e.id)
        employees.append(id)
        employee_daily_rest[id] = e.daily_rest_hours
        employee_weekly_rest[id] = e.daily_rest_hours
        employee_contracted_hours[id] = e.contracted_hours
        
    
    return employees, employee_with_competencies, employee_weekly_rest, employee_daily_rest, employee_contracted_hours



def get_durations(root):
    events = get_events(root)
    durations = {}
    possible_durations = [t/4 for t in range(6*4, 12*4)]
    
    for t in events:
        for dur in possible_durations:
            if(t+dur in events):
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
            if(t >=d*24 and t <= (24*(d+1) - time_step)):
                for dur in durations[t]:
                    shifts_per_day[d].append((t,dur))
                    shifts.append((t,dur))
            if(t > 24*d):
                continue
    return shifts, shifts_per_day

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
    time_step = get_time_steps(root)
    shifts_overlapping_t = {}
    shifts = get_durations(root)
    for t in time_periods:
        for time in shifts:
            for dur in shifts[time]:
                if(t >= time and t < time + dur):
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
                if(diff >= 6):
                    events.append((demand_days[day].start[t] + 24*day))
                    break
    return events


def get_off_shifts(root):
    events = get_start_events(root)
    off_shifts = []
    off_shifts_in_week = tupledict()
    week = 0
    off_shifts_in_week[week] = []
    for i in range(len(events)):
        for event2 in events[i:]:
            dur = event2 - events[i]
            if(events[i] >= (week+1)*24*7):
                week+=1
                off_shifts_in_week[week] = []
            if(event2 >= (week+1)*24*7):
               break
            if(dur > 70):
                break
            elif(dur>= 36):
                if((events[i], dur) not in off_shifts):
                    off_shifts_in_week[week].append((events[i], dur))
                    off_shifts.append((events[i], dur))
    return off_shifts, off_shifts_in_week

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
            if(shift[0] >= off_shift[0] and shift[0] < (off_shift[0] + off_shift[1]) or (shift[0] + shift[1]) >= off_shift[0] and (shift[0] + shift[1]) < (off_shift[0] + off_shift[1])):
                shifts_covered[off_shift].append(shift)
    return shifts_covered


def main_loader(problem_name):
    data_folder = Path(__file__).resolve().parents[2] / 'flexible_employee_scheduling_data/xml data/Real Instances/'
    problem_name = 'rproblem3'
    root = ET.parse(data_folder / (problem_name + '.xml')).getroot()


    employees, employee_with_competencies, employee_weekly_rest, employee_daily_rest, contracted_hours = get_employee_lists(root)
    time_step = get_time_steps(root)
    time_periods, time_periods_in_week = get_time_periods(root)
    demand_min, demand_ideal, demand_max = get_demand_periods(root)
    shifts, shifts_at_day = get_shift_lists(root)
    days = get_days(root)
    shifts_covered_by_off_shift = get_shifts_covered_by_off_shifts(root)
    shifts_overlapping_t = get_shifts_overlapping_t(root)
    t_in_off_shifts = get_t_covered_by_off_shifts(root)
    off_shifts, off_shift_in_week = get_off_shifts(root)
    return (employees, employee_with_competencies, employee_daily_rest, employee_weekly_rest, contracted_hours, 
            time_step, time_periods, time_periods_in_week, demand_min, demand_ideal, demand_max,
            shifts, shifts_at_day, shifts_covered_by_off_shift, shifts_overlapping_t, days,
            off_shifts, t_in_off_shifts, off_shift_in_week)
