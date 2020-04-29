import random
from preprocessing.xml_loader import *


def generate_preferences(staff, time_set, num_weekly_preferences, preferences_dur):
    """
    Generates random preferences for each employee. The result is normalized to 1
    Note: the result is identical between different runs, as using the same initial seed will
    guarantee the same result
    :param staff: data structure containing employees
    :param time_set: data structure containing time_step, weeks and needed time_periods-sets
    :param num_weekly_preferences: (min, max)-tuple representing bounds on the number of requests
    per employee per week
    :param preferences_dur: (min, max)-tuple representing bounds on the durations of the preference
    :return: a dict with keys [e][t], representing employee and time respectively
    """

    # Ensuring persistent results between different runs. The seed can be any integer
    random.seed(1)

    employees = staff["employees"]
    time_step = time_set["step"]
    time_periods = time_set["periods"][0]
    time_periods_in_day = time_set["periods"][2]
    weeks = time_set["weeks"]

    # Duration in hours is converted to duration in time_steps
    preferences_dur = [int(preferences_dur[0] / time_step), int(preferences_dur[1] / time_step)]
    preferences = initialize_preferences(employees, time_periods)

    # Generating preferences
    for employee in employees:
        number_of_preferences = 0

        for week in weeks:
            used_time_periods = []
            weekly_preferences = int(
                random.randint(num_weekly_preferences[0], num_weekly_preferences[1])
            )
            realized_dur = get_realized_durations(preferences_dur, weekly_preferences)

            for dur in realized_dur:

                # A positive value signifies preference for work, while
                # a negative value signifies preference for a free
                value = random.choice([-1, 1])

                # While-block is ensuring that preferences do not overlap each other
                while True:
                    day = random.randint(week * 7, ((week + 1) * 7) - 1)
                    end = len(time_periods_in_day[day]) - dur

                    if end <= 0:
                        dur = time_periods_in_day[day][-1] - time_periods_in_day[day][0]
                        end = len(time_periods_in_day[day]) - dur

                    start_index = random.randint(0, end)

                    time_range = time_periods_in_day[day][start_index : start_index + dur]

                    if is_unique_preference(time_range, used_time_periods):
                        break

                for t in time_periods_in_day[day][start_index : start_index + dur]:
                    preferences[employee][t] = value
                    used_time_periods.append(t)

                number_of_preferences += dur

        preferences = normalize_preferences(employee, number_of_preferences, preferences)

    return preferences


def is_unique_preference(time_range, used_time_periods):
    """ Check if the preference overlaps with any other preferences"""

    for time in time_range:
        if time in used_time_periods:
            return False
    return True


def normalize_preferences(employee, number_of_preferences, preferences):
    """ Normalizes the preferences """

    factor = 1.0 / number_of_preferences

    for elem in preferences[employee]:
        preferences[employee][elem] *= factor

    return preferences


def get_realized_durations(preferences_dur, weekly_preferences):
    """
    Generates durations for each of the preferences in weekly_preferences belonging to a particular
    employee
    """

    realized_dur = [
        random.randint(preferences_dur[0], preferences_dur[1]) for _ in range(weekly_preferences)
    ]

    return realized_dur


def initialize_preferences(employees, time_periods):
    """ Initializing all preferences """

    preferences = tupledict()

    for employee in employees:
        preferences[employee] = tupledict()

        for time in time_periods:
            preferences[employee][time] = 0

    return preferences
