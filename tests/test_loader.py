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


def test_loader_returns_employees_for_test_data(data):

    employees = loader.get_employees(data)

    assert type(employees) == dict
    assert len(employees) == 1
    assert type(employees["ScheduleRow"]) == list
