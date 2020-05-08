from gurobipy.gurobipy import GRB, quicksum


class ShiftDesignObjective:
    def __init__(self, model, var, weights, shift_sets, time_periods, competencies):
        self.model = model
        self.time_periods = time_periods

        self.shifts = shift_sets["shifts"]
        self.short_shifts = shift_sets["short_shifts"]
        self.long_shifts = shift_sets["long_shifts"]
        self.competencies = competencies
        self.add_objective(weights, var.y, var.delta, var.rho)

    def add_objective(self, weights, y, delta, rho):
        self.model.setObjective(
            quicksum(y[t, v] for t, v in self.shifts)
            + quicksum(weights["excess demand deviation factor"] * delta["plus"][c, t] +
                       weights["deficit demand deviation factor"] * delta["minus"][c, t]
                       for c in self.competencies
                       for t in self.time_periods[c])
            + (
                quicksum(weights["use of short shift"] * rho["short"][t, v] for t, v in self.short_shifts)
                + quicksum(weights["use of long shift"] * rho["long"][t, v] for t, v in self.long_shifts)
            ),
            GRB.MINIMIZE,
        )
