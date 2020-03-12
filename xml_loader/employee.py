class Employee:
    def __init__(self, nbr):
        self.id = nbr
        self.weekly_rest_hours = 36
        self.daily_rest_hours = 8
        self.competencies = []  # Default. Could also be called default directly (or another name)
        self.contracted_hours = None

    def add_weekly_rest(self, weekly_rest):
        self.weekly_rest_hours = weekly_rest

    def add_daily_rest(self, daily_rest):
        self.daily_rest_hours = daily_rest

    def set_competency(self, competency):
        self.competencies.append(competency)

    def set_contracted_hours(self, hours=38):
        self.contracted_hours = hours

    def __str__(self):
        return self.id
