class Employee():
    def __init__(self, nbr):
        self.id = nbr
        self.weekly_rest_hours = None
        self.daily_rest_hours = None
        self.competencies = [0] #Default. Could also be called default directly (or another name)
        self.contracted_hours = None

    def add_daily_rest(self, daily_rest):
        pass

    def add_weekly_rest(self, daily_rest):
        pass
        
    def set_comptency(self, competency):
        self.competencies.append(competency)
        
    def set_contracted_hours(self, hours):
        self.contracted_hours = hours

    def __str__(self):
        return self.id
