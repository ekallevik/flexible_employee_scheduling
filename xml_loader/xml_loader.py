import xml.etree.ElementTree as ET
from datetime import date, time, timedelta, datetime
import sys
from pathlib import Path
from gurobipy import *
import numpy as np
import time
loader_path = str(Path(__file__).resolve().parent)
sys.path.insert(1, loader_path)
from demand import Demand
from employee import Employee
from rest_rule import Weekly_rest_rule, Daily_rest_rule
data_folder = Path(__file__).resolve().parents[2] / 'flexible_employee_scheduling_data/xml data/Real Instances/'
root = ET.parse(data_folder / 'rproblem3.xml').getroot()
today = date.today()

def get_demand_definitions2():
    demands = []
    for DemandDefinition in root.findall('Demands/DemandDefinitions/DemandDefinition'):
        dem = Demand(DemandDefinition.find("DayDemandId").text)
        for row in DemandDefinition.find("Rows").findall("Row"):
            start = row.find("TimeStart").text
            end = row.find("TimeEnd").text
            maksimum = row.find("Max").text
            minimum = row.find("Min").text
            ideal = row.find("Ideal").text
            dem.add_info2(start, end, maksimum, minimum, ideal)
        demands.append(dem)
    return demands


def get_demand_definitions():
    demands = []
    for DemandDefinition in root.findall('Demands/DemandDefinitions/DemandDefinition'):
        dem = Demand(DemandDefinition.find("DayDemandId").text)
        for row in DemandDefinition.find("Rows").findall("Row"):
            start = row.find("TimeStart").text
            end = row.find("TimeEnd").text
            maksimum = row.find("Max").text
            minimum = row.find("Min").text
            ideal = row.find("Ideal").text
            dem.add_info(start, end, maksimum, minimum, ideal)
        demands.append(dem)
    return demands

def get_competencies():
    competencies = tuplelist()
    for competence in root.findall('Configuration/Competences/Competence'):
        id = competence.find('CompetenceId').text
        competencies.append(id)
    return competencies


def get_days_with_demand2():
    demands = get_demand_definitions2()
    days_with_demand = {}
    for day in root.findall('Demands/DayDemandList/DayDemand'):
        for obj in demands:
            if obj.demand_id == day.find("DayDemandId").text:
                day_obj = today + timedelta(days = int(day.find("DayIndex").text))
                days_with_demand[day_obj] = obj
    return days_with_demand

def get_days_with_demand():
    demands = get_demand_definitions()
    days_with_demand = {}
    for day in root.findall('Demands/DayDemandList/DayDemand'):
        for obj in demands:
            if obj.demand_id == day.find("DayDemandId").text:
                d = int(day.find("DayIndex").text)
                days_with_demand[d] = obj
    return days_with_demand

def get_days():
    days = []
    for day in root.findall('Demands/DayDemandList/DayDemand'):
        days.append(int(day.find("DayIndex").text))
    return days

def get_weekly_rest_rules():
    weekly_rest_rules = []
    for weekly_rule in root.findall('Configuration/WeeklyRestRules/WeeklyRestRule'):
        rest_id = weekly_rule.find("Id")
        hours = weekly_rule.find("MinRestHours")
        rule = Weekly_rest_rule(hours, rest_id)
        weekly_rest_rules.append(rule)
    return weekly_rest_rules

def get_daily_rest_rules():
    daily_rest_rules = []
    for daily_rule in root.findall('Configuration/DailyRestRules/DailyRestRule'):
        rest_id = daily_rule.find("Id")
        hours = daily_rule.find("MinRestHours")
        rule = Daily_rest_rule(hours, rest_id)
        daily_rest_rules.append(rule)
    return daily_rest_rules

def get_employees():
    employees = []
    competencies = get_competencies()
    weekly_rest_rules = get_weekly_rest_rules()
    Daily_rest_rules = get_daily_rest_rules()
    for schedule_row in root.findall('SchedulePeriod/ScheduleRows/ScheduleRow'):
        employee_id = schedule_row.find("RowNbr").text
        emp = Employee(employee_id)
        try: 
            contracted_hours = float(schedule_row.find("WeekHours").text)
        except AttributeError:
            print("ScheduleRow %s don't have a set WeekHours tag" % employee_id)
            contracted_hours = 36

        if(len(competencies) == 0):
            emp.set_comptency(0)
        else:
            try: 
                for competence in schedule_row.find("Competences").findall("CompetenceId"):
                    if(competence.text in competencies):
                        emp.set_comptency(competence.text)
            except AttributeError:
                print("ScheduleRow %s don't have a set Competence tag" % employee_id)
        try:
            weekly_rest_rule = schedule_row.find("WeeklyRestRule").text
            for weekly_rule in weekly_rest_rules:
                if(weekly_rule.id == weekly_rest_rule):
                    emp.add_weekly_rest(weekly_rule.hours)
        except:
            pass
        try:
            daily_rest_rule = schedule_row.find("DayRestRule1").text
            for daily_rule in Daily_rest_rules:
                if(daily_rule.id == daily_rest_rule):
                    emp.add_daily_rest(daily_rule.hours)
        except:
            pass
        
        emp.set_contracted_hours(contracted_hours)
        employees.append(emp)
    return employees




# def get_time_steps():
#     demands = get_days_with_demand()
#     time_step_length = 100
#     for demand in demands:
#         for i in range(len(demands[demand].end)):
#             if(demands[demand].end[i].minute > 0):
#                 if(demands[demand].end[i].minute == 30 and not (time_step_length <= 30)):
#                     time_step_length = 30
#                 elif(demands[demand].end[i].minute in [15,45] and not (time_step_length <= 15)):
#                     time_step_length = 15
#                 elif(demands[demand].end[i].minute < 15):
#                     time_step_length = 1
#                     break

#             if(demands[demand].start[i].minute > 0):
#                 if(demands[demand].start[i].minute == 30 and not (time_step_length <= 30)):
#                     time_step_length = 30
#                 elif(demands[demand].start[i].minute in [15,45] and not (time_step_length <= 15)):
#                     time_step_length = 15
#                 elif(demands[demand].start[i].minute < 15 ):
#                     time_step_length = 1
#                     break

#     return time_step_length

def get_time_steps():
    demands = get_demand_definitions()
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


# def get_time_periods():
#     time_periods = []
#     i = 0
#     time_step = get_time_steps()
#     demands = get_days_with_demand()
#     for dem in demands:
#         for i in range(len(demands[dem].start)):
#             time = datetime.combine(dem, demands[dem].start[i])
#             while(time.time() < demands[dem].end[i]):
#                 time_periods.append(time)
#                 time += timedelta(minutes = time_step)

#     return time_periods


def get_time_periods():
    time_periods = []
    i = 0
    time_step = get_time_steps()
    demands = get_days_with_demand()
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


def get_demand_periods():
    min_demand = tupledict()
    ideal_demand = tupledict()
    max_demand = tupledict()
    competencies = [0]
    time_step = get_time_steps()
    demands = get_days_with_demand()
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




def time_to_flyt():
    time_periods = get_time_periods()[0]
    time_flyt = []
    
    for t in time_periods:
        minutes = t.time().minute 
        if(int(minutes) == 0):
            pass
        else:
            minutes = 60/minutes
            minutes = (100/minutes)/100

        day_offset = (t.date() - today).days
        time_flyt.append(float(float(t.hour) + (minutes)) + 24*int(day_offset))
    return time_flyt


def get_events():
    events = []
    demand_days = get_days_with_demand()
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


    # time_flyt = []
    
    # for t in events:
    #     minutes = t.time().minute 
    #     if(int(minutes) == 0):
    #         pass
    #     else:
    #         minutes = 60/minutes
    #         minutes = (100/minutes)/100

    #     day_offset = (t.date() - today).days
    #     tid = float(float(t.hour) + (minutes)) + 24*int(day_offset)
    #     if tid not in time_flyt:
    #         time_flyt.append(tid)

    # return time_flyt

def get_employee_lists():
    employee_with_competencies = tupledict()
    employees = tuplelist()
    employee_weekly_rest = tupledict()
    employee_daily_rest = tupledict()
    employee_contracted_hours = tupledict()
    competencies = [0]

    emp = get_employees()
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



def get_durations():
    events = get_events()
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

def get_shift_lists():
    durations = get_durations()
    shifts_per_day = tupledict()
    shifts = tuplelist()
    days = get_days()
    time_step = get_time_steps()
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

def get_shift_list():
    shifts = tuplelist()
    dur = get_durations()
    i = 0
    for t in dur:
        for v in dur[t]:
            shifts.append(i)
            i += 1
    return shifts

def get_shifts_overlapping_t():
    time_periods = get_time_periods()[0]
    time_step = get_time_steps()
    shifts_overlapping_t = {}
    shifts = get_durations()
    for t in time_periods:
        for time in shifts:
            for dur in shifts[time]:
                if(t >= time and t < time + dur):
                    try:
                        shifts_overlapping_t[t].append((time, dur))
                    except:
                        shifts_overlapping_t[t] = [(time, dur)]
    return shifts_overlapping_t

def get_start_events():
    events = []
    demand_days = get_days_with_demand()
    for day in demand_days:
        for t in range(len(demand_days[day].start)):
            for j in range(len(demand_days[day].end)):
                diff = demand_days[day].end[j] - demand_days[day].start[t]
                if(diff >= 6):
                    events.append((demand_days[day].start[t] + 24*day))
                    break
    return events


def get_off_shifts():
    events = get_start_events()
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

    # for event in events:
    #     if(not(event >= 24*7*week and event < 24*7*(week+1))):
    #         print("next week" + str(event))
    #         week += 1
    #         off_shifts_in_week[week] = []
    #     for dur in possible_off_shift_durations:
    #         off_shifts.append((event,dur))
    #         off_shifts_in_week[week].append((event, dur))
    # return off_shifts

def get_t_covered_by_off_shifts():
    off_shifts = get_off_shifts()[0]
    t_covered = tupledict()
    time_periods = get_time_periods()[0]
    for shift in off_shifts:
        end = time_periods.index(shift[0] + shift[1])
        start = time_periods.index(shift[0])
        t_covered[shift[0], shift[1]] = time_periods[start:end]
    return t_covered


def get_shifts_covered_by_off_shifts():
    off_shifts = get_off_shifts()[0]
    shifts_covered = tupledict()
    shifts = get_shift_lists()[0]
    for off_shift in off_shifts:
        shifts_covered[off_shift] = []
        for shift in shifts:
            if(shift[0] >= off_shift[0] and shift[0] < (off_shift[0] + off_shift[1]) or (shift[0] + shift[1]) >= off_shift[0] and (shift[0] + shift[1]) < (off_shift[0] + off_shift[1])):
                shifts_covered[off_shift].append(shift)
    return shifts_covered




if __name__ == "__main__":
    #print(get_t_covered_by_off_shifts())
    print(get_employees()[0].weekly_rest_hours)
    #print(get_competencies())
    #get_time_periods()
    #shifts_covered = get_shifts_covered_by_off_shifts()
    #for shift in shifts_covered:
    #    print(len(shifts_covered[shift]))
    # for t in times:
    #     print(t, times[t])


"""
Stuff needed to run old model:
1. Shifts (Here we need to either fix model implementation or add shifts (off, on_call? on_duty?))
2. Durations. This is not included in the data and should be generated based on the demand
3. Preferences. We do not have data that includes preferences. This have to be either manually created, randomly created, randomly created and saved
4. Have to remove offsets from the model
5. Weights have to be included either in another file to be loaded in or created in another script
6. Time period sets
"""