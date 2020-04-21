from gurobipy import *

from utils.const import DESIRED_SHIFT_DURATION


class ShiftDesignConstraints:
    def __init__(
        self,
        model,
        var,
        competencies,
        demand,
        time_periods,
        shifts,
        shifts_overlapping_t,
        short_shifts,
        long_shifts,
    ):

        self.model = model
        self.competencies = competencies
        self.demand = demand
        self.time_periods = time_periods
        self.shifts = shifts
        self.shifts_overlapping_t = shifts_overlapping_t
        self.short_shifts = short_shifts
        self.long_shifts = long_shifts
        self.desired_shift_dur_low = DESIRED_SHIFT_DURATION[0]
        self.desired_shift_dur_long = DESIRED_SHIFT_DURATION[1]

        # Adding constraints
        self.add_minimum_demand_coverage(var.x)
        self.add_deviation_from_demand(var.x, var.delta)
        self.add_mapping_x_to_y(var.x, var.y)
        self.add_short_shift_duration(var.y, var.rho)
        self.add_long_shift_duration(var.y, var.rho)

    # Constraint definitions
    def add_minimum_demand_coverage(self, x):
        self.model.addConstrs(
            (
                quicksum(x[t_marked, v] for t_marked, v in self.shifts_overlapping_t[t])
                >= quicksum(self.demand["min"][c, t] for c in self.competencies)
                for t in self.time_periods
            ),
            name="minimum_demand_coverage",
        )

    def add_deviation_from_demand(self, x, delta):
        self.model.addConstrs(
            (
                quicksum(x[t_marked, v] for t_marked, v in self.shifts_overlapping_t[t])
                - quicksum(self.demand["ideal"][c, t] for c in self.competencies)
                == delta["plus"][t] - delta["minus"][t]
                for t in self.time_periods
            ),
            name="deviation_from_ideal_demand",
        )

    def add_mapping_x_to_y(self, x, y):

        # A big-M to ensure that the constraints works as designed
        M = 1000

        self.model.addConstrs(
            (x[t, v] <= M * y[t, v] for t, v in self.shifts), name="mapping_x_to_y"
        )

    def add_short_shift_duration(self, y, rho):
        self.model.addConstrs(
            (
                self.desired_shift_dur_low - v * y[t, v] == rho["low"][t, v]
                for t, v in self.short_shifts
            ),
            name="penalizing_low_dur_shifts",
        )

    def add_long_shift_duration(self, y, rho):
        self.model.addConstrs(
            (
                v * y[t, v] - self.desired_shift_dur_long == rho["long"][t, v]
                for t, v in self.long_shifts
            ),
            name="penalizing_long_dur_shifts",
        )
