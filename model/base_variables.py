from gurobipy import *


class BaseVariables:
    def __init__(self, model, competencies, staff, time_set, shifts_set, off_shifts_set):
        self.model = model

        self.competencies = competencies
        self.employees = staff["employees"]
        self.shifts = shifts_set["shifts"]
        self.off_shifts = off_shifts_set["off_shifts"]
        self.time_periods = time_set["periods"][0]
        self.days = time_set["days"]
        self.saturdays = time_set["saturdays"]
        self.sundays = time_set["sundays"]


        
        self.y = self.add_y()
        self.x = self.add_x()
        self.w = self.add_w()
        self.mu = self.add_mu()
        self.delta = self.add_delta()
        self.lam = self.add_lambda()

    def add_y(self):
        return self.model.addVars(
            self.competencies, self.employees, self.time_periods, vtype=GRB.BINARY, name="y")

    def add_x(self):
        return self.model.addVars(self.employees, self.shifts, vtype=GRB.BINARY, name="x")

    def add_w(self):
        return self.model.addVars(self.employees, self.off_shifts, vtype=GRB.BINARY, name="w")

    def add_mu(self):
        return self.model.addVars(
            self.competencies, self.time_periods, vtype=GRB.INTEGER, name="mu"
        )

    def add_delta(self):

        return {
            "plus": self.model.addVars(
                self.competencies, self.time_periods, vtype=GRB.INTEGER, name="delta_plus"
            ),
            "minus": self.model.addVars(
                self.competencies, self.time_periods, vtype=GRB.INTEGER, name="delta_minus"
            ),
        }

    def add_lambda(self):
        return self.model.addVars(self.employees, vtype=GRB.CONTINUOUS, name="lambda")
