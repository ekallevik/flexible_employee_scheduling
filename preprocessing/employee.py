

class Employee:
    def __init__(self, nbr):
        self.id = nbr
        self.weekly_rest_hours = None
        self.daily_rest_hours = None
        self.competencies = []
        self.contracted_hours = None
        self.daily_offset = None
        self.blocked_hours = []

    def set_weekly_rest(self, weekly_rest):
        self.weekly_rest_hours = weekly_rest

    def set_daily_rest(self, daily_rest):
        self.daily_rest_hours = daily_rest

    def set_competency(self, competency):
        self.competencies = competency

    def append_competency(self, competency):
        self.competencies.append(competency)

    def set_contracted_hours(self, hours):
        self.contracted_hours = hours

    def set_daily_offset(self, offset):
        self.daily_offset = offset

    def set_blocked_hours(self, blocked_hours):
        self.blocked_hours = blocked_hours

    def __str__(self):
        return self.id
