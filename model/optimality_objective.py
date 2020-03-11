from gurobipy.gurobipy import GRB, quicksum


class OptimalityObjective:

    def __init__(self, model, sets, var, weights):

        self.model = model

        self.add_fairness_score(sets, weights, var.f, var.w, var.lam, var.rho, var.q)
        self.add_lowest_fairness_score(sets, var.f, var.g)
        self.add_objective_for_optimal_solution(sets, weights, var.f, var.g, var.delta)

    def add_fairness_score(self, sets, weights, f, w, lam, rho, q):

        self.model.addConstrs(
            (
                f["plus"][e] - f["minus"][e]
                == weights["rest"]
                * quicksum(v * w[e, t, v] for t, v in sets["shifts"]["off_shifts"])
                - weights["contracted hours"] * lam[e]
                - weights["partial weekends"]
                * quicksum(rho["sat"][e, j] + rho["sun"][e, j] for j in sets["time"]["weeks"])
                - weights["isolated working days"]
                * quicksum(q["iso_work"][e, i] for i in sets["time"]["days"])
                - weights["isolated off days"]
                * quicksum(q["iso_off"][e, i] for i in sets["time"]["days"])
                - weights["consecutive days"]
                * quicksum(q["con"][e, i] for i in sets["time"]["days"])
                for e in sets["employees"]["all"]
                # todo: fiks dette.
                # - weights["backward rotation"] * k[e,i]
                # +weights["preferences"] * quicksum(pref[e,t] for t in time_periods) * quicksum(y[c,e,t] for c in sets["competencies"])
            ),
            name="fairness_score",
        )

    def add_lowest_fairness_score(self, sets, f, g):

        self.model.addConstrs(
            (g["plus"] - g["minus"] <= f["plus"][e] - f["minus"][e] for e in sets["employees"]["all"]),
            name="lowest_fairness_score",
        )

    def add_objective_for_feasible_solution(self, sets, y):

        self.model.setObjective(
            quicksum(
                quicksum(
                    quicksum(y[c, e, t] for e in sets["employees"]["all"])
                    for c in sets["competencies"]
                )
                for t in sets["time"]["periods"]
            ),
            GRB.MINIMIZE,
        )

    def add_objective_for_optimal_solution(self, sets, weights, f, g, delta):

        self.model.setObjective(
            quicksum(f["plus"][e] - f["minus"][e] for e in sets["employees"]["all"])
            + weights["lowest fairness score"] * (g["plus"] - g["minus"])
            - weights["demand_deviation"]
            * quicksum(
                quicksum(
                    delta["plus"][c, t] + delta["minus"][c, t] for t in sets["time"]["periods"]
                )
                for c in sets["competencies"]
            ),
            GRB.MAXIMIZE,
        )
