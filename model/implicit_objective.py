
from gurobipy.gurobipy import GRB, quicksum


class ImplicitObjective:
    def __init__(
        self, model, var, weights, competencies, preferences, staff, time_set, shift_durations
    ):
        self.model = model

        self.competencies = competencies
        self.employees = staff["employees"]

        self.time_periods = time_set["periods"][0]
        self.combined_time_periods = time_set["combined_time_periods"][0]
        self.every_time_period = time_set["every_time_period"]
        self.saturdays = time_set["saturdays"]
        self.days = time_set["days"]
        self.weeks = time_set["weeks"]
        self.weekly_rest = staff["employee_with_weekly_rest"]
        self.shift_durations = shift_durations

        self.add_fairness_score(weights, var.f, var.w_week, var.lam, var.rho, var.q, var.y, preferences)
        self.add_lowest_fairness_score(var.f, var.g)
        self.add_objective_for_optimal_solution(weights, var.f, var.g, var.delta)

    def add_fairness_score(self, weights, f, w_week, lam, rho, q, y, preferences):

        self.model.addConstrs(
            (
                f["plus"][e] - f["minus"][e]
                == weights["rest"] * quicksum(
                    quicksum(
                        v * w_week[e, t, v] for t in self.every_time_period
                    ) for v in self.shift_durations["weekly_off"] if v >= self.weekly_rest[e]
                )
                - weights["contracted hours"][e] * lam[e]
                - weights["partial weekends"]
                * quicksum(rho["sat"][e, i] + rho["sun"][e, i + 1] for i in self.saturdays)
                - weights["isolated working days"]
                * quicksum(q["iso_work"][e, i] for i in self.days)
                - weights["isolated off days"] * quicksum(q["iso_off"][e, i] for i in self.days)
                - weights["consecutive days"] * quicksum(q["con"][e, i] for i in self.days)
                + weights["preferences"]
                * quicksum(
                    preferences[e][t] * quicksum(y[c, e, t] for c in self.competencies if y.get((c, e, t)))
                    for t in self.combined_time_periods
                )
                for e in self.employees
            ),
            name="fairness_score",
        )

    def add_lowest_fairness_score(self, f, g):

        self.model.addConstrs(
            (g["plus"] - g["minus"] <= f["plus"][e] - f["minus"][e] for e in self.employees),
            name="lowest_fairness_score",
        )

    def add_objective_for_optimal_solution(self, weights, f, g, delta):

        self.model.setObjective(
            quicksum(f["plus"][e] - f["minus"][e] for e in self.employees)
            + weights["lowest fairness score"] * (g["plus"] - g["minus"])
            - quicksum(
                quicksum(weights["excess demand deviation factor"] * delta["plus"][c, t] +
                         weights["deficit demand deviation factor"] * delta["minus"][c, t]
                         for t in self.time_periods[c])
                for c in self.competencies
            ),
            GRB.MAXIMIZE,
        )
