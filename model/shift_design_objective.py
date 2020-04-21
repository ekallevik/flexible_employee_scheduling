from gurobipy.gurobipy import GRB, quicksum


class ShiftDesignObjective:
    def __init__(self, model, var, weights, shift_sets, time_periods):
        self.model = model
        self.time_periods = time_periods

        self.shifts = shift_sets["shifts"]
        self.short_shifts = shift_sets["short_shifts"]
        self.long_shifts = shift_sets["long_shifts"]

        self.add_objective(weights, var.y, var.delta, var.rho)

    def add_objective(self, weights, y, delta, rho):
        self.model.setObjective(
            quicksum(y[t, v] for t, v in self.shifts)
            + weights["demand_deviation"]
            * quicksum(delta["plus"][t] + delta["minus"][t] for t in self.time_periods)
            + weights["shift_dur"]
            * (
                quicksum(rho["short"][t, v] for t, v in self.short_shifts)
                + quicksum(rho["long"][t, v] for t, v in self.long_shifts)
            ),
            GRB.MINIMIZE,
        )
