import xml.etree.ElementTree as ET
import datetime
from pathlib import Path

data_folder = Path(__file__).resolve().parents[2]


class demand():

    def __init__(self, demand_id):
        self.demand_id = demand_id
        self.start = []
        self.end = []
        self.minimum = []
        self.maks = [] 
        self.ideal = []

    def add_info(self, start, end, maksimum, minimum, ideal):
        start = start.split(":")
        end = end.split(":")
        self.start.append(datetime.time(int(start[0]),int(start[1])))
        self.end.append(datetime.time(int(end[0]),int(end[1])))
        self.minimum.append(int(minimum))
        self.maks.append(int(maksimum))
        self.ideal.append(int(ideal))

    def __str__(self):
        return(self.demand_id)


def get_demand():
    root = ET.parse(data_folder / 'flexible_employee_scheduling_data/xml data/Real Instances/rproblem3.xml').getroot()
    demands = []
    i = 0

    for DemandDefinition in root.findall('Demands/DemandDefinitions/DemandDefinition'):
        demands.append(demand(DemandDefinition.find("DayDemandId").text))
        for row in DemandDefinition.find("Rows").findall("Row"):
            start = row.find("TimeStart").text
            end = row.find("TimeEnd").text
            maksimum = row.find("Max").text
            minimum = row.find("Min").text
            ideal = row.find("Ideal").text
            demands[i].add_info(start, end, maksimum, minimum, ideal)
        i+=1

    days_with_demand = {}
    for day in root.findall('Demands/DayDemandList/DayDemand'):
        for obj in demands:
            if obj.demand_id == day.find("DayDemandId").text:
                days_with_demand[day.find("DayIndex").text] = obj
    return days_with_demand
