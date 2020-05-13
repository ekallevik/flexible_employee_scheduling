from gurobipy import *


class ShiftDesignVariables:
    def __init__(self, model, shift_sets, time_periods, time_periods_combined, competencies):

        self.model = model

        self.shifts = shift_sets["shifts"]
        self.short_shifts = shift_sets["short_shifts"]
        self.long_shifts = shift_sets["long_shifts"]

        self.time_periods = time_periods
        self.time_periods_combined = time_periods_combined
        self.competencies = competencies

        self.x = self.add_x()
        self.y = self.add_y()
        self.mu = self.add_mu()
        self.delta = self.add_delta()
        self.rho = self.add_rho()

    def add_x(self):
        return self.model.addVars(self.shifts, vtype=GRB.INTEGER, name="x")

    def add_y(self):
        return self.model.addVars(self.shifts, vtype=GRB.BINARY, name="y")

    def add_mu(self):
        return self.model.addVars(self.time_periods_combined, vtype=GRB.INTEGER, name="mu")

    def add_delta(self):
        plus = {(c, t): 0 for c in self.competencies for t in self.time_periods[c]}
        minus = {(c, t): 0 for c in self.competencies for t in self.time_periods[c]}
        return {
            "plus": self.model.addVars(plus, vtype=GRB.INTEGER, name="delta_plus"),
            "minus": self.model.addVars(minus, vtype=GRB.INTEGER, name="delta_minus"),
        }

    def add_rho(self):
        return {
            "short": self.model.addVars(self.short_shifts, vtype=GRB.CONTINUOUS, name="rho_short"),
            "long": self.model.addVars(self.long_shifts, vtype=GRB.CONTINUOUS, name="rho_long"),
        }
