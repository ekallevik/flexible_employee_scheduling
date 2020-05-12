import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from gurobipy.gurobipy import tupledict, tuplelist
from datetime import timedelta, datetime
today = datetime.today()
from collections import defaultdict
from loguru import logger

from preprocessing.demand import Demand
from preprocessing.employee import Employee
from preprocessing.rest_rule import Daily_rest_rule, Weekly_rest_rule
from itertools import chain, combinations
from utils.const import (
    DEFAULT_COMPETENCY,
    DEFAULT_CONTRACTED_HOURS,
    DEFAULT_DAILY_OFFSET,
    DEFAULT_DAILY_REST_HOURS,
)


def get_employee_lists(root, competencies):
    employees = tuplelist()
    employee_with_competencies = tupledict()
    employee_weekly_rest = tupledict()
    employee_daily_rest = tupledict()
    employee_contracted_hours = tupledict()
    employee_daily_offset = tupledict()
    employee_blocked_hours = tupledict()

    emp = get_staff(root, competencies)


    for c in range(len(competencies)):
        employee_with_competencies[c] = []
        for e in emp:
            if c in e.competencies:
                employee_with_competencies[c].append(int(e.id))

    for e in emp:
        id = int(e.id)
        employees.append(id)
        employee_daily_rest[id] = e.daily_rest_hours
        employee_weekly_rest[id] = e.weekly_rest_hours
        employee_contracted_hours[id] = e.contracted_hours
        employee_daily_offset[id] = e.daily_offset
        employee_blocked_hours[id] = e.blocked_hours

    return {
        "employees": employees,
        "employees_with_competencies": employee_with_competencies,
        "employee_with_weekly_rest": employee_weekly_rest,
        "employee_daily_rest": employee_daily_rest,
        "employee_contracted_hours": employee_contracted_hours,
        "employee_daily_offset": employee_daily_offset,
        "employee_blocked_hours": employee_blocked_hours,
        "employee_with_competency_combination": get_competency_combinations(emp),
    }


def get_staff(root, all_competencies):
    weekly_rest_rules = get_weekly_rest_rules(root)
    daily_rest_rules = get_daily_rest_rules(root)
    staff = []
    for schedule_row in root.findall("SchedulePeriod/ScheduleRows/ScheduleRow"):
        employee = Employee(schedule_row.find("RowNbr").text)

        set_contracted_hours_for_employee(employee, schedule_row)
        set_weekly_rest_rule_for_employee(employee, schedule_row, weekly_rest_rules)
        set_daily_rest_rule(daily_rest_rules, employee, schedule_row)
        set_daily_offset_for_employee(employee)
        set_blocked_hours_for_employee(employee)

        competencies = []
        try:
            for competency in schedule_row.find("competencies").findall("CompetenceId"):
                competencies.append(int(competency.text))
                if int(competency.text) not in all_competencies:
                    all_competencies.append(int(competency.text))
        except:
            competencies = DEFAULT_COMPETENCY
            if(DEFAULT_COMPETENCY[0] not in all_competencies):
                all_competencies.append(DEFAULT_COMPETENCY[0])
        employee.set_competencies(competencies)
        staff.append(employee)
    return staff

def get_competency_combinations(employees):
    competency_combinations = defaultdict(list)
    for e in employees:
        competency_combos_for_e = list(chain.from_iterable(combinations(e.competencies, r) for r in range(1,len(e.competencies)+1)))
        for comp in competency_combos_for_e:
            competency_combinations[comp].append((len(e.competencies),int(e.id)))
    return competency_combinations


def set_contracted_hours_for_employee(employee, schedule_row):
    try:
        employee.set_contracted_hours(float(schedule_row.find("WeekHours").text))
    except AttributeError:
        logger.info(
            f"ScheduleRow {employee.id} don't have WeekHours tag. DEFAULT_CONTRACTED_HOURS applied"
        )
        employee.set_contracted_hours(DEFAULT_CONTRACTED_HOURS)


def get_days_with_demand(root):
    demands = get_demand_definitions(root)
    days_with_demand = {}
    for day in root.findall('Demands/DayDemandList/DayDemand'):
        for obj in demands:
            if obj.demand_id == day.find("DayDemandId").text:
                d = int(day.find("DayIndex").text)
                days_with_demand[d] = obj
    return days_with_demand


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
            try:
                for requirement in row.find("CompetenceRequirements").findall("CompetenceId"):
                    # if int(requirement.text) not in competencies:
                    #     raise AttributeError("No employee with this competency")
                    competency_requirements = int(requirement.text)
            except:
                competency_requirements = DEFAULT_COMPETENCY[0]
            dem.add_info(start, end, maximum, minimum, ideal, competency_requirements)
        demands.append(dem)
    return demands



def get_days(root):
    days = []
    for day in root.findall("Demands/DayDemandList/DayDemand"):
        days.append(int(day.find("DayIndex").text))
    return days


def set_daily_rest_rule(daily_rest_rules, employee, schedule_row):
    try:
        daily_rest_rule = schedule_row.find("DayRestRule").text
        for daily_rule in daily_rest_rules:
            if daily_rule.rest_id == daily_rest_rule:
                employee.set_daily_rest(daily_rule.hours)
    except AttributeError:
        logger.info(
            f"ScheduleRow {employee.id} don't have a set DayRestRule tag. Using DEFAULT_DAILY_REST"
        )
        employee.set_daily_rest(DEFAULT_DAILY_REST_HOURS)


def set_weekly_rest_rule_for_employee(employee, schedule_row, weekly_rest_rules):
    try:
        weekly_rest_rule = schedule_row.find("WeeklyRestRule").text
        for weekly_rule in weekly_rest_rules:
            if weekly_rule.rest_id == weekly_rest_rule:
                employee.set_weekly_rest(weekly_rule.hours)
    except AttributeError:
        logger.info(
            f"ScheduleRow {employee.id} don't have WeeklyRestRule tag. DEFAULT_WEEKLY_REST applied"
        )
        employee.set_daily_rest(DEFAULT_DAILY_REST_HOURS)


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


def set_daily_offset_for_employee(employee):
    # TODO: Implement try-block, trying to collect daily offset from file.
    employee.set_daily_offset(DEFAULT_DAILY_OFFSET)


def set_blocked_hours_for_employee(employee):
    # TODO: Implement code to retrieve blocked hours from xml. If there is no data to retrieve,
    #  nothing should be done as default blocked hours is initialized to an empty list in
    #  employee-class.
    pass


def get_root(problem):

    data_folder = get_data_folder(problem)

    return ET.parse(data_folder / (problem + ".xml")).getroot()


def get_data_folder(problem):

    if "rproblem" in problem:
        data_folder = (
            Path(__file__).resolve().parents[2]
            / "flexible_employee_scheduling_data/xml data/Real Instances/"
        )
    elif "problem" in problem:
        data_folder = (
            Path(__file__).resolve().parents[2]
            / "flexible_employee_scheduling_data/xml data/Artificial Instances/"
        )
    else:
        raise ValueError(
            "Not a valid problem! The problem_name should include 'problem' or 'rproblem'"
        )

    return data_folder


def get_demand_definitions2(root):
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

def get_days_with_demand2(root):
    demands = get_demand_definitions2(root)
    days_with_demand = {}
    for day in root.findall('Demands/DayDemandList/DayDemand'):
        for obj in demands:
            if obj.demand_id == day.find("DayDemandId").text:
                day_obj = today + timedelta(days = int(day.find("DayIndex").text))
                days_with_demand[day_obj] = obj
    return days_with_demand