from gurobipy import *

from utils.const import DESIRED_SHIFT_DURATION


class ShiftDesignConstraints:
    def __init__(
        self, model, var, competencies, demand, time_periods, shift_sets, time_periods_combined
    ):

        self.model = model
        self.competencies = competencies
        self.demand = demand
        self.time_periods = time_periods
        self.time_periods_combined = time_periods_combined

        self.shifts = shift_sets["shifts"]
        self.shifts_overlapping_t = shift_sets["shifts_overlapping_t"]
        self.short_shifts = shift_sets["short_shifts"]
        self.long_shifts = shift_sets["long_shifts"]

        # Adding constraints
        self.add_minimum_demand_coverage(var.x, var.mu)
        self.add_maximum_demand_coverage(var.mu)
        self.add_deviation_from_demand(var.x, var.delta)
        self.add_mapping_x_to_y(var.x, var.y)
        self.add_short_shift_duration(var.y, var.rho)
        self.add_long_shift_duration(var.y, var.rho)

    # Constraint definitions
    def add_minimum_demand_coverage(self, x, mu):
        self.model.addConstrs(
            (
                quicksum(x[t_marked, v] for t_marked, v in self.shifts_overlapping_t[t])
                == quicksum(self.demand["min"][c, t] for c in self.competencies if self.demand["min"].get((c, t)))
                + mu[t]
                for t in self.time_periods_combined
            ),
            name="minimum_demand_coverage",
        )

    def add_maximum_demand_coverage(self, mu):
        self.model.addConstrs(
            (
                mu[t] <= quicksum(self.demand["max"][c, t] - self.demand["min"][c, t] for c in self.competencies)
                for t in self.time_periods_combined
            ),
            name="maximum_demand_coverage"
        )

    def add_deviation_from_demand(self, mu, delta):
        self.model.addConstrs(
            (
                mu[t]
                + self.demand["min"][c, t]
                - self.demand["ideal"][c, t]
                == delta["plus"][c, t] - delta["minus"][c, t]
                for c in self.competencies
                for t in self.time_periods[c]
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
                (DESIRED_SHIFT_DURATION[0] - v) * y[t, v] == rho["short"][t, v]
                for t, v in self.short_shifts
            ),
            name="penalizing_short_shift_duration",
        )

    def add_long_shift_duration(self, y, rho):
        self.model.addConstrs(
            (
                (v - DESIRED_SHIFT_DURATION[1]) * y[t, v] == rho["long"][t, v]
                for t, v in self.long_shifts
            ),
            name="penalizing_long_shift_duration",
        )
