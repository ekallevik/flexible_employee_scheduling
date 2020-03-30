from gurobipy.gurobipy import GRB, quicksum


class OptimalityObjective:
    def __init__(self, model, var, weights, competencies, staff, time, off_shift_set, saturdays):
        self.model = model

        self.competencies = competencies
        self.employees = staff["employees"]

        self.time_periods = time_set["periods"][0]
        self.days = time_set["days"]
        self.weeks = time_set["weeks"]
        self.off_shifts = off_shift_set["off_shifts"]
        self.saturdays = saturdays

        self.add_fairness_score(weights, var.f, var.w, var.lam, var.rho, var.q)
        self.add_lowest_fairness_score(var.f, var.g)
        self.add_objective_for_optimal_solution(weights, var.f, var.g, var.delta)

    def add_fairness_score(self, weights, f, w, lam, rho, q):

        self.model.addConstrs(
            (
                f["plus"][e] - f["minus"][e]
                == weights["rest"] * quicksum(v * w[e, t, v] for t, v in self.off_shifts)
                - weights["contracted hours"] * lam[e]
                - weights["partial weekends"]
                * quicksum(rho["sat"][e, i] + rho["sun"][e, i+1] for i in self.saturdays)
                - weights["isolated working days"]
                * quicksum(q["iso_work"][e, i] for i in self.days)
                - weights["isolated off days"] * quicksum(q["iso_off"][e, i] for i in self.days)
                - weights["consecutive days"] * quicksum(q["con"][e, i] for i in self.days)
                for e in self.employees
            ),
            name="fairness_score",
        )

    def add_lowest_fairness_score(self, f, g):

        self.model.addConstrs(
            (g["plus"] - g["minus"] <= f["plus"][e] - f["minus"][e] for e in self.employees),
            name="lowest_fairness_score",
        )

    def add_objective_for_feasible_solution(self, y):

        self.model.setObjective(
            quicksum(
                quicksum(quicksum(y[c, e, t] for e in self.employees) for c in self.competencies)
                for t in self.time_periods
            ),
            GRB.MINIMIZE,
        )

    def add_objective_for_optimal_solution(self, weights, f, g, delta):

        self.model.setObjective(
            quicksum(f["plus"][e] - f["minus"][e] for e in self.employees)
            + weights["lowest fairness score"] * (g["plus"] - g["minus"])
            - weights["demand_deviation"]
            * quicksum(
                quicksum(delta["plus"][c, t] + delta["minus"][c, t] for t in self.time_periods[0])
                for c in self.competencies
            ),
            GRB.MAXIMIZE,
        )
