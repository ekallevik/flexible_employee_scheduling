import xml.etree.ElementTree as ET
from datetime import date, time, timedelta, datetime
from pathlib import Path

data_folder = Path(__file__).resolve().parents[2]
today = date.today()
root = ET.parse(data_folder / 'flexible_employee_scheduling_data/xml data/Real Instances/rproblem2.xml').getroot()
time_step_length = None





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

def get_time_steps():
    time_step_length = None
    demands = get_demand()
    for demand in demands:
        for i in range(len(demands[demand].end)):
            if(demands[demand].end[i].minute == 30 or demands[demand].start[i].minute == 30):
                print("Var 30 minutter her")

"""                
if(int(start[1]) > 0):
    if(int(start[1]) == 30 or end[1] == 30):
        print("Inneholder halvtimer")
    elif(int(start[1] == 45 or start[1] == 15 or end[1] == 15 or end[1] == 45):
        print("Inneholder kvarterer")
    else:
        print("Inneholder minutter")
"""




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


if __name__ == "__main__":
    #Sets i Need:
    employee_ids = []
    employee_competencies = []


    for e in get_employees():
        employee_ids.append(int(e.id))
        employee_competencies.append(e.competencies)

get_demand()
print(get_time_steps())
#get_daily_rest_rules()
#get_weekly_rest_rules()
#for e in get_employees():
 #   print(e.contracted_hours)



"""
Stuff needed to run old model:
1. Shifts (Here we need to either fix model implementation or add shifts (off, on_call? on_duty?))
2. Durations. This is not included in the data and should be generated based on the demand
3. Preferences. We do not have data that includes preferences. This have to be either manually created, randomly created, randomly created and saved
4. Have to remove offsets from the model
5. Weights have to be included either in another file to be loaded in or created in another script
"""