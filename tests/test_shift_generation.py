import pytest
import sys
from pathlib import Path
loader_path = Path(__file__).resolve().parents[1]
sys.path.insert(1, str(loader_path))
from xml_loader.shift_generation import *
import xml.etree.ElementTree as ET
data_folder = Path(__file__).resolve().parents[2] / 'flexible_employee_scheduling_data/xml data/Artifical Test Instances/'


@pytest.fixture
def time_step():
    root = ET.parse(data_folder / ('problem12.xml')).getroot()
    time_step = get_time_steps(root)
    return time_step

@pytest.fixture
def time_periods():
    root = ET.parse(data_folder / ('problem12.xml')).getroot()
    days = get_days(root)
    time_periods, time_periods_in_week = get_time_periods(root)
    return time_periods, time_periods_in_week, days

@pytest.fixture
def durations():
    root = ET.parse(data_folder / ('problem12.xml')).getroot()
    return get_durations(root)



def test_time_step(time_step):
    assert time_step == 1, "Expected time step of 1 hour got %d" % (time_step)


def test_time_periods(time_periods):
    assert time_periods[0][0] == 96
    assert time_periods[0][-1] == len(time_periods[2])*24 - 1


def test_durations(durations):
    print(durations)
    fail()