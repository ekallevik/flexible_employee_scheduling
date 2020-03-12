import pytest

from xml_loader.shift_generation import *

loader_path = Path(__file__).resolve().parents[1]
sys.path.insert(1, str(loader_path))

data_folder = (
        Path(__file__).resolve().parents[2]
        / "flexible_employee_scheduling_data/xml data/Artifical Test Instances/"
)


@pytest.fixture
def time_step():
    root = ET.parse(data_folder / "problem12.xml").getroot()
    time_step = get_time_steps(root)
    return time_step


@pytest.fixture
def time_periods():
    root = ET.parse(data_folder / "problem12.xml").getroot()
    days = get_days(root)
    time_periods, time_periods_in_week = get_time_periods(root)
    return time_periods, time_periods_in_week, days


@pytest.fixture
def durations():
    # Possible to run on any dataset. Depends on get_events being correct
    root = ET.parse(data_folder / "problem12.xml").getroot()
    return get_durations(root), get_events(root)


@pytest.fixture
def events():
    root = ET.parse(data_folder / "problem12.xml").getroot()
    return get_events(root)


@pytest.fixture
def shifts():
    # Possible to run on any dataset. Dependent on get_durations being correct
    root = ET.parse(data_folder / "problem12.xml").getroot()
    return get_shift_lists(root), get_durations(root)


def test_time_step(time_step):
    assert time_step == 1, "Expected time step of 1 hour got %d" % time_step


def test_time_periods(time_periods):
    assert time_periods[0][0] == 0
    assert time_periods[0][-1] == len(time_periods[2]) * 24 - 1


def test_events(events):
    assert events == ([0.0, 12.0, 24.0, 36.0, 48.0, 60.0, 72.0, 84.0, 96.0, 102.0, 108.0, 114.0, 120.0, 126.0, 132.0,
                       138.0, 144.0, 150.0, 156.0, 162.0, 168.0]), "The created events are incorrect"


def test_durations(durations):
    for t in durations[0]:
        ind = durations[1].index(t)
        for length in range(len(durations[0][t])):
            assert durations[0][t][length] == (durations[1][ind + (length + 1)] - durations[1][ind])


def test_shifts(shifts):
    for shift in shifts[0][0]:
        assert shift[0] in shifts[1]
        assert shift[1] in shifts[1][shift[0]]
