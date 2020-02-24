import xml.etree.ElementTree as ET
from datetime import date, time, timedelta, datetime
import sys
sys.path.insert(1, '/Users/hakongrov/Documents/Code/Masteroppgave/flexible_employee_scheduling/xml_loader')
from pathlib import Path
from demand import Demand
from employee import Employee
from rest_rule import Weekly_rest_rule, Daily_rest_rule


data_folder = Path(__file__).resolve().parents[2] / 'flexible_employee_scheduling_data/xml data/Real Instances/'
root = ET.parse(data_folder / 'rproblem3.xml').getroot()
today = date.today()

# def get_demand_definitions():
#     demands = []
#     for DemandDefinition in root.findall('Demands/DemandDefinitions/DemandDefinition'):
#         dem = Demand(DemandDefinition.find("DayDemandId").text)
#         for row in DemandDefinition.find("Rows").findall("Row"):
#             start = row.find("TimeStart").text
#             end = row.find("TimeEnd").text
#             maksimum = row.find("Max").text
#             minimum = row.find("Min").text
#             ideal = row.find("Ideal").text
#             dem.add_info(start, end, maksimum, minimum, ideal)
#         demands.append(dem)
#     return demands


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


# def get_days_with_demand():
#     demands = get_demand_definitions()
#     days_with_demand = {}
#     for day in root.findall('Demands/DayDemandList/DayDemand'):
#         for obj in demands:
#             if obj.demand_id == day.find("DayDemandId").text:
#                 day_obj = today + timedelta(days = int(day.find("DayIndex").text))
#                 days_with_demand[day_obj] = obj
#     return days_with_demand

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
                elif(demand.end[i] - int(demand.end[i]) == 0.25 and time_step_length != 0.25):
                    time_step_length = 0.25
                elif(demand.end[i] - int(demand.end[i]) < 0.25):
                    time_step_length = 100/60
                    break
            if(demand.start[i] - int(demand.start[i]) > 0):
                if(demand.start[i] - int(demand.start[i]) == 0.5 and time_step_length != 0.5):
                    time_step_length = 0.5
                elif(demand.start[i] - int(demand.start[i]) == 0.25 and time_step_length != 0.25):
                    time_step_length = 0.25
                elif(demand.start[i] - int(demand.start[i]) < 0.25):
                    time_step_length = 100/60
                    break
    return time_step_length


def get_time_periods():
    time_periods = []
    i = 0
    time_step = get_time_steps()
    demands = get_days_with_demand()
    for dem in demands:
        for i in range(len(demands[dem].start)):
            time = datetime.combine(dem, demands[dem].start[i])
            while(time.time() < demands[dem].end[i]):
                time_periods.append(time)
                time += timedelta(minutes = time_step)

    return time_periods


def get_demand_periods():
    min_demand = []
    ideal_demand = []
    max_demand = []
    competencies = [0]
    time_step = get_time_steps()
    demands = get_days_with_demand()


    for c in range(len(competencies)):
        for dem in demands:
            for i in range(len(demands[dem].start)):
                time = datetime.combine(dem, demands[dem].start[i])
                while(time.time() < demands[dem].end[i]):
                    time += timedelta(minutes = time_step)
                    min_demand.append(demands[dem].minimum[i])
                    ideal_demand.append(demands[dem].ideal[i])
                    max_demand.append(demands[dem].maks[i])
    return min_demand, ideal_demand, max_demand



def get_employees():
    employees = []
    for schedule_row in root.findall('SchedulePeriod/ScheduleRows/ScheduleRow'):
        employee_id = schedule_row.find("RowNbr").text
        try: 
            contracted_hours = float(schedule_row.find("WeekHours").text)
        except AttributeError:
            print("ScheduleRow %s don't have a set WeekHours tag" % employee_id)

        emp = Employee(employee_id)
        emp.set_contracted_hours(contracted_hours)
        employees.append(emp)
    return employees


def get_weekly_rest_rules():
    weekly_rest_rules = []
    for weekly_rule in root.findall('Configuration/WeeklyRestRules/WeeklyRestRule'):
        rest_id = weekly_rule.find("Id")
        hours = weekly_rule.find("MinRestHours")
        rule = weekly_rest_rule(hours, rest_id)
        weekly_rest_rules.append(rule)
    return weekly_rest_rules

def get_daily_rest_rules():
    daily_rest_rules = []
    for daily_rule in root.findall('Configuration/DailyRestRules/DailyRestRule'):
        rest_id = daily_rule.find("Id")
        hours = daily_rule.find("MinRestHours")
        rule = daily_rest_rule(hours, rest_id)
        daily_rest_rules.append(rule)
    return daily_rest_rules



def time_to_flyt():
    time_periods = get_time_periods()
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
    time_step = get_time_steps()
    for key in demand_days:
        for t in range(len(demand_days[key].start)):
            time = datetime.combine(key, demand_days[key].start[t])
            events.append(time)
            time = datetime.combine(key, demand_days[key].end[t]) - timedelta(minutes = time_step)
            events.append(time)

    time_flyt = []
    
    for t in events:
        minutes = t.time().minute 
        if(int(minutes) == 0):
            pass
        else:
            minutes = 60/minutes
            minutes = (100/minutes)/100

        day_offset = (t.date() - today).days
        tid = float(float(t.hour) + (minutes)) + 24*int(day_offset)
        if tid not in time_flyt:
            time_flyt.append(tid)

    return time_flyt

def get_employee_competencies():
    employee_with_competencies = []
    employee_ids = []
    contracted_hours = []
    competencies = [0]
    for c in range(len(competencies)):
        employee_with_competencies.append([])
        for e in get_employees():
           # print(e.competencies)
            if(c in e.competencies):
                employee_with_competencies[c].append(int(e.id))
            employee_ids.append(int(e.id))
            contracted_hours.append(e.contracted_hours)
    return employee_with_competencies, employee_ids, contracted_hours


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

def get_shifts_at_days():
    durations = get_durations()
    #print(durations.keys())
    shifts = {}
    days = get_days()
    time_step = (100/(60/get_time_steps()))/100
    for d in days:
        for t in durations:
            if(t >=(d-1)*24 and t <= (24*d - time_step)):
                try:
                    shifts[d].append((t,durations[t]))
                except:
                    shifts[d] = [(t,durations[t])]
            if(t > 24*d):
                continue
    return shifts


def get_shifts_overlapping_t():
    time_periods = time_to_flyt()
    time_step = (100/(60/get_time_steps()))/100
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
                        


if __name__ == "__main__":
    print(get_time_steps())
    #Sets I Need:
    #Durations v of shifts indexed by a time t
    # durations = {}
    # #An array containing id's of employees (from 1 to number of employees)
    # employee_ids = []
    # #The competency of the employee at the index
    # employee_competencies = []
    # #Contracted hours of the employee at the index
    # contracted_hours = []
    # #Number of days in the planning period
    # days = []
    # #All the individual time periods where there is demand with time step equal to the shortest demand periods
    # time_periods = time_to_flyt()
    # #Min/max/ideal demand for each time period
    # min_demand, ideal_demand, max_demand = get_demand_periods()
    # #Events where a demand begins or ends (Endings have time step subtracted)

    # dur = get_durations()
    # #print(len(dur.keys()))

    # get_shifts_at_days()
    # get_shifts_overlapping_t()
    



    
#get_daily_rest_rules()
#get_weekly_rest_rules()



"""
Stuff needed to run old model:
1. Shifts (Here we need to either fix model implementation or add shifts (off, on_call? on_duty?))
2. Durations. This is not included in the data and should be generated based on the demand
3. Preferences. We do not have data that includes preferences. This have to be either manually created, randomly created, randomly created and saved
4. Have to remove offsets from the model
5. Weights have to be included either in another file to be loaded in or created in another script
6. Time period sets
"""