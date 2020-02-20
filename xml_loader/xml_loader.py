import xml.etree.ElementTree as ET
from datetime import date, time, timedelta, datetime
from pathlib import Path

data_folder = Path(__file__).resolve().parents[2]
today = date.today()
root = ET.parse(data_folder / 'flexible_employee_scheduling_data/xml data/Real Instances/rproblem4.xml').getroot()


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
        self.competency = None
        self.contracted_hours = None

    def add_daily_rest(self, daily_rest):
        pass

    def add_weekly_rest(self, daily_rest):
        pass
        
    def set_comptency(self, competency):
        pass
        
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


def get_demand():
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

    days_with_demand = {}
    for day in root.findall('Demands/DayDemandList/DayDemand'):
        for obj in demands:
            if obj.demand_id == day.find("DayDemandId").text:
                days_with_demand[day.find("DayIndex").text] = obj
    return days_with_demand



def get_employees():
    employees = []
    for schedule_row in root.findall('SchedulePeriod/ScheduleRows/ScheduleRow'):
        employee_id = schedule_row.find("RowNbr").text
        contracted_hours = float(schedule_row.find("WeekHours").text)

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


get_demand()
get_daily_rest_rules()
get_weekly_rest_rules()
for e in get_employees():
    print(e.contracted_hours)