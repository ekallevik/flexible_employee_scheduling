import pytest

from preprocessing import xml_loader
from utils.const import DAYS_IN_WEEK, DEFAULT_COMPETENCY


def test_loading_demand():

    root = xml_loader.get_root("problem12")
    demand_definitions = xml_loader.get_demand_definitions(root)

    assert len(demand_definitions) == 2, "Should be two demand definitions"

    dem1 = demand_definitions[0]
    dem2 = demand_definitions[1]

    assert dem1.start == [0, 0], "Demand 1 should have two demands starting at 00:00"
    assert dem2.start == [
        0,
        6,
        12,
        18,
    ], "Demand 2 should have demands starting at [00:00, 06:00, 12:00, 18:00]"

    assert dem1.end == [0, 0]
    assert dem2.end == [6, 12, 18, 0]

    assert dem1.minimum == [1, 2]
    assert dem1.ideal == [2, 3]
    assert dem1.maximum == [3, 4]

    assert dem2.minimum == [1, 2, 3, 4]
    assert dem2.ideal == [2, 3, 4, 5]
    assert dem2.maximum == [3, 4, 5, 6]


def test_rest_rules():

    root = xml_loader.get_root("problem19")
    daily_rest_rules = xml_loader.get_daily_rest_rules(root)
    weekly_rest_rules = xml_loader.get_weekly_rest_rules(root)

    competencies = xml_loader.get_competencies(root)
    staff = xml_loader.get_staff(root, competencies)

    assert weekly_rest_rules[0].rest_id == "WeeklyRestRule1"

    for employee in staff:
        assert employee.weekly_rest_hours == 36
        assert employee.daily_rest_hours == 9


@pytest.mark.parametrize(
    "problem, expected",
    [
        ("rproblem", "flexible_employee_scheduling_data/xml data/Real Instances"),
        ("problem", "flexible_employee_scheduling_data/xml data/Artificial Instances"),
    ],
)
def test_get_data_folder(problem, expected):

    folder = xml_loader.get_data_folder(problem).as_posix()

    assert type(folder) == str
    assert expected in folder


@pytest.mark.parametrize(
    "problem, expected",
    [
        ("rproblem2", DEFAULT_COMPETENCY),
        ("rproblem3", DEFAULT_COMPETENCY),
        ("problem12", ["Competence1", "Competence2", "Competence3"]),
    ],
)
def test_get_competencies(problem, expected):

    root = xml_loader.get_root(problem)
    competencies = xml_loader.get_competencies(root)

    assert competencies == expected


@pytest.mark.parametrize(
    "problem, expected",
    [
        ("rproblem2", [i for i in range(10 * DAYS_IN_WEEK)]),
        ("rproblem3", [i for i in range(4 * DAYS_IN_WEEK)]),
        ("problem12", [i for i in range(7)]),
    ],
)
def test_get_days(problem, expected):

    root = xml_loader.get_root(problem)
    days = xml_loader.get_days(root)

    assert days == expected


@pytest.mark.parametrize(
    "problem, expected_number, expected_contracted, expected_competencies",
    [("problem12", 1, 37, ["Competence1", "Competence2", "Competence3"])],
)
def test_get_staff(problem, expected_number, expected_contracted, expected_competencies):

    root = xml_loader.get_root(problem)
    competencies = xml_loader.get_competencies(root)
    staff = xml_loader.get_staff(root, competencies)

    assert len(staff) == expected_number
    assert staff[0].contracted_hours == expected_contracted
    assert staff[0].competencies == expected_competencies


@pytest.mark.parametrize(
    "problem, expected",
    [
        (
            "problem12",
            [
                "DayDemandId1",
                "DayDemandId1",
                "DayDemandId1",
                "DayDemandId1",
                "DayDemandId2",
                "DayDemandId2",
                "DayDemandId2",
            ],
        )
    ],
)
def test_get_days_with_demand(problem, expected):

    root = xml_loader.get_root(problem)
    days_with_demand = xml_loader.get_days_with_demand(root)

    demand_ids = [day_demand.demand_id for day_demand in days_with_demand.values()]

    assert demand_ids == expected
