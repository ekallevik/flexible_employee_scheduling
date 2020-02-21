import xml.etree.ElementTree as ET
from datetime import date, time, timedelta, datetime
from pathlib import Path

data_folder = Path(__file__).resolve().parents[2]
root = ET.parse(data_folder / 'flexible_employee_scheduling_data/xml data/Real Instances/rproblem3.xml').getroot()
today = date.today()


class weekly_rest_rule():
    def __init__(self, hours, rest_id):
        self.rest_id = rest_id
        self.hours = hours

class daily_rest_rule():
    def __init__(self, hours, rest_id):
        self.rest_id = rest_id
        self.hours = hours

class employee():
    def __init__(self, nbr):
        self.id = nbr
        self.weekly_rest_hours = None
        self.daily_rest_hours = None
        self.competencies = [0] #Default. Could also be called default directly (or another name)
        self.contracted_hours = None

    def add_daily_rest(self, daily_rest):
        pass

    def add_weekly_rest(self, daily_rest):
        pass
        
    def set_comptency(self, competency):
        self.competencies.append(competency)
        
    def set_contracted_hours(self, hours):
        self.contracted_hours = hours

    def __str__(self):
        return self.id

class demand():

    def __init__(self, demand_id):
        self.demand_id = demand_id
        self.start = []
        self.end = []
        self.minimum = []
        self.maks = [] 
        self.ideal = []
        self.time_delta = []
        self.time_step_length = None
    
    def add_info(self, start, end, maksimum, minimum, ideal):
        start = start.split(":")
        end = end.split(":")
        start = time(int(start[0]), int(start[1]))
        end = time(int(end[0]), int(end[1]))
        self.start.append(start)
        self.end.append(end)
        self.minimum.append(int(minimum))
        self.maks.append(int(maksimum))
        self.ideal.append(int(ideal))
        self.time_delta.append(datetime.combine(today, end) - datetime.combine(today,start))


    def __str__(self):
        return(self.demand_id)


def get_demand_definitions():
    demands = []
    for DemandDefinition in root.findall('Demands/DemandDefinitions/DemandDefinition'):
        dem = demand(DemandDefinition.find("DayDemandId").text)
        for row in DemandDefinition.find("Rows").findall("Row"):
            start = row.find("TimeStart").text
            end = row.find("TimeEnd").text
            maksimum = row.find("Max").text
            minimum = row.find("Min").text
            ideal = row.find("Ideal").text
            dem.add_info(start, end, maksimum, minimum, ideal)
        demands.append(dem)
    return demands

def get_days_with_demand():
    days = []
    demands = get_demand_definitions()
    #print(demands)
    days_with_demand = {}
    for day in root.findall('Demands/DayDemandList/DayDemand'):
        days.append(int(day.find("DayIndex").text))
        for obj in demands:
            if obj.demand_id == day.find("DayDemandId").text:
                day_obj = today + timedelta(days = int(day.find("DayIndex").text))
                days_with_demand[day_obj] = obj
    return days_with_demand


def get_time_steps():
    demands = get_days_with_demand()
    time_step_length = 100
    for demand in demands:
        for i in range(len(demands[demand].end)):
            if(demands[demand].end[i].minute > 0):
                if(demands[demand].end[i].minute == 30 and not (time_step_length <= 30)):
                    time_step_length = 30
                elif(demands[demand].end[i].minute in [15,45] and not (time_step_length <= 15)):
                    time_step_length = 15
                elif(demands[demand].end[i].minute < 15):
                    time_step_length = 1
                    break

            if(demands[demand].start[i].minute > 0):
                if(demands[demand].start[i].minute == 30 and not (time_step_length <= 30)):
                    time_step_length = 30
                elif(demands[demand].start[i].minute in [15,45] and not (time_step_length <= 15)):
                    time_step_length = 15
                elif(demands[demand].start[i].minute < 15 ):
                    time_step_length = 1
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

    time_step = get_time_steps()
    demands = get_days_with_demand()
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

        emp = employee(employee_id)
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

def get_daily_rest_rules():
    daily_rest_rules = []
    for daily_rule in root.findall('Configuration/DailyRestRules/DailyRestRule'):
        rest_id = daily_rule.find("Id")
        hours = daily_rule.find("MinRestHours")
        rule = daily_rest_rule(hours, rest_id)
        daily_rest_rules.append(rule)

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
    #print(time_flyt)

if __name__ == "__main__":
    #Sets i Need:
    employee_ids = []
    employee_competencies = []
    contracted_hours = []
    days = []
    time_periods = time_to_flyt()
    min_demand, ideal_demand, max_demand = get_demand_periods()
    for e in get_employees():
        employee_ids.append(int(e.id))
        employee_competencies.append(e.competencies)
        contracted_hours.append(e.contracted_hours)

    



    
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