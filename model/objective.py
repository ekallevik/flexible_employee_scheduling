from gurobipy.gurobipy import quicksum, GRB


def add_objective(model, sets, weights, variables, find_optimal_solution=True):

    y, x, w, mu, delta, gamma, lam, rho, q, f, g = variables.values()

    if find_optimal_solution:
        add_fairness_score(model, sets, weights, f, w, lam, rho, q)
        add_lowest_fairness_score(model, sets, f, g)
        add_objective_for_optimal_solution(model, sets, weights, f, g, delta)
    else:
        add_objective_for_feasible_solution(model, sets, y)


def add_fairness_score(model, sets, weights, f, w, lam, rho, q):

    model.addConstrs(
        (
            f["plus"][e] - f["minus"][e]
            == weights["rest"] * quicksum(v * w[e, t, v] for t, v in sets["shifts"]["off_shifts"])
            - weights["contracted hours"] * lam[e]
            - weights["partial weekends"]
            * quicksum(rho["sat"][e, j] + rho["sun"][e, j] for j in sets["time"]["weeks"])
            - weights["isolated working days"]
            * quicksum(q["iso_work"][e, i] for i in sets["time"]["days"])
            - weights["isolated off days"]
            * quicksum(q["iso_off"][e, i] for i in sets["time"]["days"])
            - weights["consecutive days"] * quicksum(q["con"][e, i] for i in sets["time"]["days"])
            for e in sets["employees"]
            # todo: fiks dette.
            # - weights["backward rotation"] * k[e,i]
            # +weights["preferences"] * quicksum(pref[e,t] for t in time_periods) * quicksum(y[c,e,t] for c in sets["competencies"])
        ),
        name="fairness_score",
    )


def add_lowest_fairness_score(model, sets, f, g):
    model.addConstrs(
        (g["plus"] - g["minus"] <= f["plus"][e] - f["minus"][e] for e in sets["employees"]),
        name="lowest_fairness_score",
    )


def add_objective_for_feasible_solution(model, sets, y):

    model.setObjective(
        quicksum(
            quicksum(quicksum(y[c, e, t] for e in sets["employees"]["all"]) for c in sets["competencies"])
            for t in sets["time"]["periods"]
        ),
        GRB.MINIMIZE,
    )


def add_objective_for_optimal_solution(model, sets, weights, f, g, delta):

    model.setObjective(
        quicksum(f["plus"][e] - f["minus"][e] for e in sets["employees"])
        + weights["lowest fairness score"] * (g["plus"] - g["minus"])
        - weights["demand_deviation"]
        * quicksum(
            quicksum(delta["plus"][c, t] + delta["minus"][c, t] for t in sets["time"]["periods"])
            for c in sets["competencies"]
        ),
        GRB.MAXIMIZE,
    )
