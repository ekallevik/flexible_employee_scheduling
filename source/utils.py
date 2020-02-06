
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
