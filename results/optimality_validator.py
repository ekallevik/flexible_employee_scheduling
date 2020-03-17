class OptimalityValidator:

    def __init__(self, gamma, employees, days):
        self.gamma = gamma
        self.employees = employees
        self.days = days

    def count_consecutive_day_violations(self, working_days, consecutive_day_limit):

        violations = 0

        for day in range(len(working_days) - consecutive_day_limit + 1):
            if self.violates_consecutive_days(working_days[day:day+consecutive_day_limit], consecutive_day_limit):
                violations += 1

        return violations

    def violates_consecutive_days(self, working_days, consecutive_day_limit):

        if len(working_days) != consecutive_day_limit:
            raise ValueError("The number of days must match the limit")

        return sum(working_days) == consecutive_day_limit


    def count_isolated_days_violations(self, working_days):

        violations = {"working_days": 0, "off_days": 0}

        for day in range(len(working_days) - 2):
            time_slice = working_days[day:day+3]
            if self.violates_isolated_working_days(time_slice):
                violations["working_days"] += 1
            elif self.violates_isolated_off_days(time_slice):
                violations["off_days"] += 1

        return violations

    def violates_isolated_working_days(self, working_days):

        if len(working_days) != 3:
            raise ValueError("The number of days must match the limit")

        return working_days[0] == 0 and working_days[1] == 1 and working_days[2] == 0


    def violates_isolated_off_days(self, working_days):

        if len(working_days) != 3:
            raise ValueError("The number of days must match the limit")

        return working_days[0] == 1 and working_days[1] == 0 and working_days[2] == 1

    def is_last_working_day_a_sunday(self, working_days, saturdays):
        """
        The last Sunday is 1 index after the last Saturday. In addition, working days is
        0-indexed, which means an offset of 1. In total the offset is therefore 2.
        """

        return len(working_days) == saturdays[-1] + 2

    def count_partial_weekend_violations(self, working_days, saturdays):

        print(working_days)
        print(saturdays)
        print(saturdays[-1])
        print(working_days[saturdays[-1]])
        print(len(working_days))

        if not self.is_last_working_day_a_sunday(working_days, saturdays):
            raise ValueError("The last working day is not a Sunday")

        violations = 0

        for saturday in saturdays:
            if self.violates_partial_weekends(working_days[saturday:saturday+2]):
                violations += 1

        return violations

    def violates_partial_weekends(self, weekend):

        if len(weekend) != 2:
            raise ValueError("The weekend should consist of exactly two days")

        return weekend[0] != weekend[1]
