
from gurobipy import *


class ShiftDesignVariables:
    def __init__(self, model, shifts, time_periods):
        self.model = model
        self.shifts = shifts
        self.time_periods = time_periods

        self.x = self.add_x()
        self.y = self.add_y()
        self.delta = self.add_delta()

    def add_x(self):
        return self.model.addVars(self.shifts, vtype=GRB.INTEGER, name="x")

    def add_y(self):
        return self.model.addVars(self.shifts, vtype=GRB.BINARY, name="y")

    def add_delta(self):
        return {
            "plus": self.model.addVars(
                self.time_periods, vtype=GRB.INTEGER, name="delta_plus"
            ),
            "minus": self.model.addVars(
                self.time_periods, vtype=GRB.INTEGER, name="delta_minus"
            ),
        }

