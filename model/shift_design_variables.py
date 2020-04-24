from gurobipy import *


class ShiftDesignVariables:
    def __init__(self, model, shift_sets, time_periods):

        self.model = model

        self.shifts = shift_sets["shifts"]
        self.short_shifts = shift_sets["short_shifts"]
        self.long_shifts = shift_sets["long_shifts"]

        self.time_periods = time_periods

        self.x = self.add_x()
        self.y = self.add_y()
        self.delta = self.add_delta()
        self.rho = self.add_rho()

    def add_x(self):
        return self.model.addVars(self.shifts, vtype=GRB.INTEGER, name="x")

    def add_y(self):
        return self.model.addVars(self.shifts, vtype=GRB.BINARY, name="y")

    def add_delta(self):
        return {
            "plus": self.model.addVars(self.time_periods, vtype=GRB.INTEGER, name="delta_plus"),
            "minus": self.model.addVars(self.time_periods, vtype=GRB.INTEGER, name="delta_minus"),
        }

    def add_rho(self):
        return {
            "short": self.model.addVars(self.short_shifts, vtype=GRB.CONTINUOUS, name="rho_short"),
            "long": self.model.addVars(self.long_shifts, vtype=GRB.CONTINUOUS, name="rho_long"),
        }
