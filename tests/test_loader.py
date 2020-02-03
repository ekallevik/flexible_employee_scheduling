from unittest import mock

import pytest

import loader


@pytest.fixture()
@mock.patch("loader.BASE_DIR", "../../flexible_employee_scheduling_data")
def data():
    return loader.load_xml_into_dict()


@pytest.fixture()
@mock.patch("loader.BASE_DIR", "../../flexible_employee_scheduling_data")
def real_data():
    return loader.load_xml_into_dict(real_mode=True)


def test_loader_can_load_artificial_problem(data):

    assert type(data) == dict


def test_loader_can_load_real_problem(real_data):

    assert type(real_data) == dict


def test_loader_returns_schedule_info(data):

    schedule_info = loader.get_schedule_info(data)

    assert schedule_info["number_of_weeks"] == 2
    assert len(schedule_info.keys()) == 1


def test_loader_returns_employees_for_test_data(data):

    employees = loader.get_employees(data)

    assert type(employees) == dict
    assert len(employees) == 1
    assert type(employees["ScheduleRow"]) == list


def test_loader_returns_employees_for_real_data(real_data):

    employees = loader.get_employees(data)

    print(employees)

    assert type(employees) == dict
    assert len(employees) == 1
    assert type(employees["ScheduleRow"]) == list
