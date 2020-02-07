from unittest import mock
import pytest

from source import loader


@pytest.fixture()
def expected_formatted_definitions():
    return {
        'DayDemandId1': [
            {'TimeStart': [10, 0], 'TimeEnd': [15, 0], 'Type': 'WORK', 'Min': 1, 'Ideal': 2, 'Max': 3},
            {'TimeStart': [14, 0], 'TimeEnd': [18, 15], 'Type': 'WORK', 'Min': 1, 'Ideal': 2, 'Max': 3}],
        'DayDemandId2': [
            {'TimeStart': [10, 0], 'TimeEnd': [18, 0], 'Type': 'WORK', 'Min': 1, 'Ideal': 2, 'Max': 3}]}


@pytest.fixture()
def expected_aggregated_definitions():
    return {
            'DayDemandId1': {
                'Min': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                'Ideal': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 4, 2, 2, 2, 0, 0, 0, 0, 0, 0],
                'Max': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 6, 3, 3, 3, 0, 0, 0, 0, 0, 0],
            },
            'DayDemandId2': {
                'Min': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                'Ideal': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0],
                'Max': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0],
            }
    }


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


@pytest.mark.parametrize("time, round_up, time_step, expected", [
    [[9, 13], True, 1, [9, 13]],
    [[9, 13], True, 15, [9, 15]],
    [[9, 13], True, 30, [9, 30]],
    [[9, 13], True, 60, [10, 00]],
    [[15, 47], False, 1, [15, 47]],
    [[15, 47], False, 15, [15, 45]],
    [[15, 47], False, 30, [15, 30]],
    [[15, 47], False, 60, [15, 00]]
])
def test_adjust_times(time, round_up, time_step, expected):
    actual_time = loader.adjust_times(time, round_up, time_step)

    assert actual_time == expected


@pytest.mark.parametrize("task, time_step, expected", [
    [{'TimeStart': '09:13', 'TimeEnd': '15:47'}, 1, {'TimeStart': [9, 13], 'TimeEnd': [15, 47]}],
    [{'TimeStart': '09:13', 'TimeEnd': '15:47'}, 15, {'TimeStart': [9, 15], 'TimeEnd': [15, 45]}],
    [{'TimeStart': '09:13', 'TimeEnd': '15:47'}, 60, {'TimeStart': [10, 00], 'TimeEnd': [15, 00]}]
])
def test_format_task(task, time_step, expected):
    formatted_task = loader.format_task(task, time_step=time_step)

    assert formatted_task == expected


def test_format_demand_definitions(data, expected_formatted_definitions):

    actual_formatted_definitions = loader.format_demand_definitions(data["Demands"]["DemandDefinitions"]["DemandDefinition"])

    assert actual_formatted_definitions == expected_formatted_definitions


@pytest.mark.parametrize("time, time_step, expected", [
    [[0, 0], 30, 0],
    [[0, 30], 30, 1],
    [[1, 0], 30, 2],
    [[1, 30], 30, 3]
])
def test_convert_time_to_index(time, time_step, expected):

    index = loader.convert_time_to_index(time, time_step)

    assert index == expected


@pytest.mark.parametrize("task, time_step, expected", [
    [{'TimeStart': [5, 0], 'TimeEnd': [15, 30]}, 30, range(10, 31)],
    [{'TimeStart': [0, 0], 'TimeEnd': [2, 0]}, 30, range(0, 4)]
])
def test_get_time_range_for_task(task, time_step, expected):

    task_range = loader.get_time_range_for_task(task, time_step)

    assert task_range == expected


def test_aggregate_definitions(data, expected_aggregated_definitions):

    aggregated_definitions = loader.aggregate_definitions(data["Demands"]["DemandDefinitions"]["DemandDefinition"],
                                                          time_step=60)

    print(f"\nA = {aggregated_definitions}")
    print(f"\nE = {expected_aggregated_definitions}")

    assert len(expected_aggregated_definitions["DayDemandId1"]["Min"]) == 24
    assert aggregated_definitions == expected_aggregated_definitions



def test_aggregate_demand(data):

    # todo: refactor
    demand = loader.aggregate_demand(data, number_of_days=14, time_step=60)


    assert False

def test_get_day_size():
    assert False

def test_get_initialized_demand_dict():
    assert False