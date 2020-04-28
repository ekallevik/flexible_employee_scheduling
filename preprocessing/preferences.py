
import random
from preprocessing.xml_loader import *


def generate_preferences(staff, time_set, num_weekly_preferences, preferences_dur):
    """
    Generates random preferences for each employee. The result is normalized to 1
    Note: the result is identical between different runs, as using the same initial seed will guarantee the same result
    :param employees: a list of all employees
    :param time_periods: a dict containing all time periods
    :param requests: a (min, max)-tuple representing bounds on the number of requests per employee
    :param durations: a (min, max)-tuple representing bounds on the durations of the preference
    :param number_of_weeks: the number of weeks the schedules should apply to
    :return:
    """

    # Ensuring persistent results between different runs. The seed can be any integer
    random.seed(1)
    preferences = tupledict()

    employees = staff["employees"]
    time_step = time_set["step"]
    time_periods = time_set["periods"][0]
    time_periods_in_day = time_set["periods"][2]
    weeks = time_set["weeks"]

    preferences_dur = [int(preferences_dur[0]/time_step), int(preferences_dur[1]/time_step)]

    # Initializing all preferences
    for employee in employees:
        preferences[employee] = tupledict()

        for time in time_periods:
            preferences[employee][time] = 0

    for employee in employees:
        number_of_preferences = 0

        for week in weeks:
            used_time_periods = []
            weekly_preferences = int(random.randint(num_weekly_preferences[0], num_weekly_preferences[1]))
            realized_dur = [random.randint(preferences_dur[0], preferences_dur[1]) for i in range(weekly_preferences)]

            for dur in realized_dur:
                value = random.choice([-1, 1])
                unique_preference = False

                while not unique_preference:
                    day = random.randint(week * 7, ((week + 1) * 7) - 1)
                    unique_preference = True
                    try:
                        start_index = random.randint(0, len(time_periods_in_day[day]) - dur)
                    except:
                        dur = time_periods_in_day[day][-1] - time_periods_in_day[day][0]
                        start_index = random.randint(0, len(time_periods_in_day[day]) - dur)

                    for time in time_periods_in_day[day][start_index:start_index + dur]:
                        if time in used_time_periods:
                            unique_preference = False
                            break

                for t in time_periods_in_day[day][start_index:start_index + dur]:
                    preferences[employee][t] = value
                    used_time_periods.append(t)

                number_of_preferences += dur

        factor = 1.0/number_of_preferences

        for elem in preferences[employee]:
            preferences[employee][elem] *= factor

    return preferences


