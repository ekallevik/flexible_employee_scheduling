
from gurobipy.gurobipy import GRB, quicksum


class ShiftDesignObjective:
    def __init__(self, model, var, weights, shifts, time_periods):
        self.model = model
        self.shifts = shifts
        self.time_periods = time_periods

        self.add_objective(weights, var.y, var.delta)

    def add_objective(self, weights, y, delta):
        self.model.setObjective(
            quicksum(y[t_marked, v] for t_marked, v in self.shifts) +
            weights["demand_deviation"] * quicksum(delta["plus"][t] + delta["minus"][t] for t in self.time_periods),
            GRB.MINIMIZE,
        )

