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

