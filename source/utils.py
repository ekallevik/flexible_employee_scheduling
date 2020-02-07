from source.const import HOURS_IN_A_DAY, MINUTES_IN_A_HOUR


def time_generator(time_start, time_step, time_end):
    """
    Yields successive times by iteratively adding time_step to time_start. Stops the iterating before time_end is
    reached.

    Args:
        time_start: The starting time for the iterator. Format [hour, min].
        time_step: The length of the time step in minutes.
        time_end: The stopping criteria of the iterator. Not included.

    Returns: A time time_step minutes later than the previous returned value.

    """

    time = time_start

    while time != time_end:

        yield time

        time[1] += time_step
        if time[1] == 60:
            time = [time[0] + 1, 0]


def times_in_day(day, time_step):

    day_size = get_day_size(time_step)

    for time in range(day_size):
        yield day * day_size + time


def get_day_size(time_step):
    return int(HOURS_IN_A_DAY * MINUTES_IN_A_HOUR / time_step)