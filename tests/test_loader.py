from unittest import mock
import pytest

import loader


@pytest.fixture()
@mock.patch.object(loader, "BASE_DIR", "./tests")
def data():
    return loader.load_xml_into_dict()


def test_loader_can_load_data(data):

    assert type(data) == dict


def test_loader_returns_schedule_info(data):

    schedule_info = loader.get_schedule_info(data)

    assert schedule_info["number_of_weeks"] == 2
    assert len(schedule_info.keys()) == 1


def test_loader_returns_employee_info(data):

    number_of_employees, working_hours, competencies = loader.get_employee_info(data)

    assert number_of_employees == 2

    assert working_hours == [14, 28]

    assert len(competencies.keys()) == 2
    assert competencies["Competence1"] == [0, 1]
    assert competencies["Competence2"] == [0]


def test_get_tasks(data):

    tasks = loader.get_tasks(demand_definitions=data["Demands"]["DemandDefinitions"]["DemandDefinition"])

    assert len(tasks) == 1
    assert len(tasks["DayDemandId1"]) == 2


@pytest.mark.parametrize("time, round_up, time_step, expected", [
    [(9, 13), True, 1, (9, 13)],
    [(9, 13), True, 15, (9, 15)],
    [(9, 13), True, 30, (9, 30)],
    [(9, 13), True, 60, (10, 00)],
    [(15, 47), False, 1, (15, 47)],
    [(15, 47), False, 15, (15, 45)],
    [(15, 47), False, 30, (15, 30)],
    [(15, 47), False, 60, (15, 00)]
])
def test_adjust_times(time, round_up, time_step, expected):

    actual_time = loader.adjust_times(time, round_up, time_step)

    assert actual_time == expected



