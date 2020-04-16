
from gurobipy.gurobipy import GRB, quicksum


class ShiftDesignObjective:
    def __init__(self, model, var, weights, shifts, time_periods, low_dur_shifts, long_dur_shifts):
        self.model = model
        self.shifts = shifts
        self.time_periods = time_periods
        self.low_dur_shifts = low_dur_shifts
        self.long_dur_shifts = long_dur_shifts

        self.add_objective(weights, var.y, var.delta, var.rho)

    def add_objective(self, weights, y, delta, rho):
        self.model.setObjective(
            quicksum(y[t_1, v_1] for t_1, v_1 in self.shifts) +
            weights["demand_deviation"] * quicksum(delta["plus"][t] + delta["minus"][t] for t in self.time_periods) +
            weights["shift_dur"] * (
                    quicksum(rho["low"][t_2, v_2] for t_2, v_2 in self.low_dur_shifts) +
                    quicksum(rho["long"][t_3, v_3] for t_3, v_3 in self.long_dur_shifts)
                    ),
            GRB.MINIMIZE,
        )

