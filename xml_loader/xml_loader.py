import xml.etree.ElementTree as ET
from pathlib import Path

from utils.const import DEFAULT_COMPETENCY
from xml_loader.demand import Demand
from xml_loader.employee import Employee
from xml_loader.rest_rule import Weekly_rest_rule, Daily_rest_rule


def get_demand_definitions(root):
    demands = []
    for DemandDefinition in root.findall("Demands/DemandDefinitions/DemandDefinition"):
        dem = Demand(DemandDefinition.find("DayDemandId").text)
        for row in DemandDefinition.find("Rows").findall("Row"):
            start = row.find("TimeStart").text
            end = row.find("TimeEnd").text
            maximum = row.find("Max").text
            minimum = row.find("Min").text
            ideal = row.find("Ideal").text
            dem.add_info(start, end, maximum, minimum, ideal)
        demands.append(dem)
    return demands


def get_competencies(root):
    competencies = []
    for competence in root.findall("Configuration/Competences/Competence"):
        id = competence.find("CompetenceId").text
        competencies.append(id)

    if not competencies:
        competencies = DEFAULT_COMPETENCY

    return competencies


def get_days_with_demand(root):
    demands = get_demand_definitions(root)
    days_with_demand = {}
    for day in root.findall("Demands/DayDemandList/DayDemand"):
        for obj in demands:
            if obj.demand_id == day.find("DayDemandId").text:
                d = int(day.find("DayIndex").text)
                days_with_demand[d] = obj
    return days_with_demand


def get_days(root):
    days = []
    for day in root.findall("Demands/DayDemandList/DayDemand"):
        days.append(int(day.find("DayIndex").text))
    return days


def get_weekly_rest_rules(root):
    weekly_rest_rules = []
    for weekly_rule in root.findall("Configuration/WeeklyRestRules/WeeklyRestRule"):
        rest_id = weekly_rule.find("Id").text
        hours = weekly_rule.find("MinRestHours").text
        rule = Weekly_rest_rule(hours, rest_id)
        weekly_rest_rules.append(rule)
    return weekly_rest_rules


def get_daily_rest_rules(root):
    daily_rest_rules = []
    for daily_rule in root.findall("Configuration/DayRestRules/DayRestRule"):
        rest_id = daily_rule.find("Id").text
        hours = daily_rule.find("MinRestHours").text
        rule = Daily_rest_rule(hours, rest_id)
        daily_rest_rules.append(rule)
    return daily_rest_rules


def get_employees(root, competencies):
    weekly_rest_rules = get_weekly_rest_rules(root)
    daily_rest_rules = get_daily_rest_rules(root)
    employees = []
    for schedule_row in root.findall("SchedulePeriod/ScheduleRows/ScheduleRow"):
        employee_id = schedule_row.find("RowNbr").text
        emp = Employee(employee_id)
        try:
            contracted_hours = float(schedule_row.find("WeekHours").text)
        except AttributeError:
            print("ScheduleRow %s don't have a set WeekHours tag" % employee_id)
            contracted_hours = 36

        if len(competencies) == 0:
            emp.set_competency(0)
        else:
            try:
                for competence in schedule_row.find("Competences").findall("CompetenceId"):
                    if competence.text in competencies:
                        emp.set_competency(competence.text)
            except AttributeError:
                print("ScheduleRow %s don't have a set Competence tag" % employee_id)
        try:
            weekly_rest_rule = schedule_row.find("WeeklyRestRule").text
            for weekly_rule in weekly_rest_rules:
                if weekly_rule.rest_id == weekly_rest_rule:
                    emp.add_weekly_rest(weekly_rule.hours)
        except:
            pass
        try:
            daily_rest_rule = schedule_row.find("DayRestRule").text
            for daily_rule in daily_rest_rules:
                if daily_rule.rest_id == daily_rest_rule:
                    emp.add_daily_rest(daily_rule.hours)
        except:
            pass

        emp.set_contracted_hours(contracted_hours)
        employees.append(emp)
    return employees


def get_root(problem_name):
    data_folder = (
        Path(__file__).resolve().parents[2]
        / "flexible_employee_scheduling_data/xml data/Real Instances/"
    )
    root = ET.parse(data_folder / (problem_name + ".xml")).getroot()
    return root
