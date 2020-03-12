import pytest
import sys
from pathlib import Path

loader_path = Path(__file__).resolve().parents[1]
sys.path.insert(1, str(loader_path))
from xml_loader.xml_loader import *
import xml.etree.ElementTree as ET

data_folder = (
    Path(__file__).resolve().parents[2]
    / "flexible_employee_scheduling_data/xml data/Artifical Test Instances/"
)


@pytest.fixture
def competencies():
    root = ET.parse(data_folder / "problem12.xml").getroot()
    competencies = get_competencies(root)
    return competencies


@pytest.fixture
def days():
    root = ET.parse(data_folder / "problem12.xml").getroot()
    days = get_days(root)
    return days


@pytest.fixture
def employees():
    root = ET.parse(data_folder / "problem12.xml").getroot()
    competencies = get_competencies(root)
    employees = get_employees(root, competencies)
    return employees


@pytest.fixture
def days_with_demand():
    root = ET.parse(data_folder / "problem12.xml").getroot()
    return get_days_with_demand(root)


@pytest.fixture
def demand_definitions():
    root = ET.parse(data_folder / "problem12.xml").getroot()
    return get_demand_definitions(root)


@pytest.fixture
def rest_rules():
    root = ET.parse(data_folder / "problem19.xml").getroot()
    competencies = get_competencies(root)
    return (
        get_weekly_rest_rules(root),
        get_daily_rest_rules(root),
        get_employees(root, competencies),
    )


def test_loading_competencies(competencies):
    assert len(competencies) == 3, "Expected 3 competencies got %d" % (len(competencies))


def test_loading_days(days):
    assert len(days) == 7, "Expected 7 days got %d" % (len(days))


def test_loading_employees(employees):
    assert len(employees) == 1, "Expected 1 employee got %d" % (len(employees))
    for employee in employees:
        assert employee.competencies == [
            "Competence1",
            "Competence2",
            "Competence3",
        ], "Employee 1 should have three competencies"
        assert employee.contracted_hours == 37, "Employee 1 should have 37 contracted hours"


def test_days_with_demand(days_with_demand):
    for day in range(4):
        assert (
            days_with_demand[day].demand_id == "DayDemandId1"
        ), "Expect the correct demand definition for the first four days"
    for day in range(4, len(days_with_demand)):
        assert (
            days_with_demand[day].demand_id == "DayDemandId2"
        ), "Expect the correct demand definition for the last three days"


def test_loading_demand(demand_definitions):
    assert len(demand_definitions) == 2, "Should be two demand definitions"

    dem1 = demand_definitions[0]
    dem2 = demand_definitions[1]

    assert dem1.start == [0, 0], "Demand 1 should have two demands starting at 00:00"
    assert dem2.start == [0, 6, 12, 18], "Demand 2 should have demands starting at [00:00, 06:00, 12:00, 18:00]"

    assert dem1.end == [0, 0]
    assert dem2.end == [6, 12, 18, 0]

    assert dem1.minimum == [1, 2]
    assert dem1.ideal == [2, 3]
    assert dem1.maximum == [3, 4]

    assert dem2.minimum == [1, 2, 3, 4]
    assert dem2.ideal == [2, 3, 4, 5]
    assert dem2.maximum == [3, 4, 5, 6]


def test_rest_rules(rest_rules):
    assert rest_rules[0][0].rest_id == "WeeklyRestRule1"
    assert rest_rules[1][0].rest_id == "DayRestRule1"

    for employee in rest_rules[2]:
        assert employee.weekly_rest_hours == 36
        assert employee.daily_rest_hours == 9
