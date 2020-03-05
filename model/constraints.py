from gurobipy import *


def add_constraints(model, sets, variables):

    add_hard_constraints(model, sets, variables)


def add_hard_constraints(model, sets, variables):

    y, x, w, mu, delta, gamma, lam, rho, q, f, g = variables.values()

    add_minimum_demand_coverage(model, sets, y, mu)


def add_soft_constraints(model, sets, variables):

    raise NotImplementedError


def add_minimum_demand_coverage(model, sets, y, mu):

    model.addConstrs(
        (
            quicksum(y[c, e, t] for e in sets["employees"]["competency"][c])
            == sets["demand"]["min"][c, t] + mu[c, t]
            for c in sets["competencies"]
            for t in sets["time"]["periods"]
        ),
        name="minimum_demand_coverage",
    )


def add_maximum_demand_coverage(model, sets, mu):

    model.addConstrs(
        (
            mu[c, t] <= sets["demand"]["max"][c, t] - sets["demand"]["min"][c, t]
            for c in sets["competencies"]
            for t in sets["time"]["periods"]
        ),
        name="mu_less_than_difference",
    )


def add_deviation_from_ideal_demand(model, sets, mu):

    model.addConstrs(
        (
            mu[c, t] + sets["demand"]["min"][c, t] - sets["demand"]["ideal"][c, t]
            == sets["delta"]["plus"][c, t] - sets["delta"]["minus"][c, t]
            for t in sets["time"]["periods"]
            for c in sets["competencies"]
        ),
        name="deviation_from_ideal_demand",
    )


def add_maximum_one_shift_each_day(model, sets, x):

    model.addConstrs(
        (
            quicksum(x[e, t, v] for t, v in sets["shifts"]["day"][i]) <= 1
            for e in sets["employees"]["all"]
            for i in sets["time"]["days"]
        ),
        name="cover_maximum_one_shift",
    )


def add_mapping_of_shift_to_demand(model, sets, x, y):

    model.addConstrs(
        (
            quicksum(x[e, t_marked, v] for t_marked, v in shifts_overlapping_t[t])
            == quicksum(y[c, e, t] for c in sets["competencies"])
            for e in sets["employees"]
            for t in sets["time_periods"]
        ),
        name="mapping_shift_to_demand",
    )


def add_max_one_demand_cover_each_time(model, sets, y):

    model.addConstrs(
        (
            quicksum(y[c, e, t] for c in sets["competencies"]) <= 1
            for e in sets["employees"]
            for t in sets["time_periods"]
        ),
        name="only_cover_one_demand_at_a_time",
    )


def add_helping_variable_gamma(model, sets, x, gamma):
    model.addConstrs(
        (
            quicksum(x[e, t, v] for t, v in sets["shifts"]["day"][i]) == gamma[e, i]
            for e in sets["employees"]
            for i in sets["days"]
        ),
        name="if_employee_e_works_day_i",
    )


def add_weekly_rest(model, sets, w):

    model.addConstrs(
        (
            quicksum(w[e, t, v] for t, v in sets["shifts"]["off_shift_in_week"][j]) == 1
            for e in sets["employees"]
            for j in sets["weeks"]
        ),
        name="one_weekly_off_shift_per_week",
    )


def add_no_demand_cover_during_off_shift(model, sets, w, y):

    model.addConstrs(
        (
            len(t_in_off_shifts[t, v]) * w[e, t, v]
            <= quicksum(
                quicksum((1 - y[c, e, t_mark]) for c in sets["competencies"])
                for t_mark in t_in_off_shifts[t, v]
            )
            for e in sets["employees"]
            for t, v in sets["shifts"]["off"]
        ),
        name="no_work_during_off_shift",
    )

    # todo: fix this before merging! -Even, 5. March
    # Alternativ 2 til off_shift restriksjon (restriksjon 1.10). Virker raskere
    model.addConstrs(
        (
            len(shifts_covered_by_off_shift[t, v]) * w[e, t, v]
            <= quicksum(
                quicksum((1 - x[e, t_marked, v_marked]) for c in sets["competencies"])
                for t_marked, v_marked in shifts_covered_by_off_shift[t, v]
            )
            for e in sets["employees"]
            for t, v in off_shifts
        ),
        name="no_work_during_off_shift",
    )

model.addConstrs(
    (
        quicksum(
            quicksum(time_step * y[c, e, t] for t in time_periods) for c in sets["competencies"]
        )
        + lam[e]
        == len(weeks) * contracted_hours[e]
        for e in sets["employees"]
    ),
    name="contracted_hours",
)

# Soft Constraints

model.addConstrs(
    (
        quicksum(
            quicksum(time_step * y[c, e, t] for t in time_periods_in_week[j])
            for c in sets["competencies"]
        )
        >= 0.1 * contracted_hours[e]
        for e in sets["employees"]
        for j in weeks
    ),
    name="min_weekly_work_hours",
)

model.addConstrs(
    (
        quicksum(
            quicksum(time_step * y[c, e, t] for t in time_periods_in_week[j])
            for c in sets["competencies"]
        )
        <= 1.4 * contracted_hours[e]
        for e in sets["employees"]
        for j in weeks
    ),
    name="maximum_weekly_work_hours",
)

model.addConstrs(
    (
        gamma[e, i] - gamma[e, (i + 1)] == ro_sat[e, i] - ro_sun[e, (i + 1)]
        for e in sets["employees"]
        for i in saturdays
    ),
    name="partial_weekends",
)

model.addConstrs(
    (
        -gamma[e, i] + gamma[e, (i + 1)] - gamma[e, (i + 2)] <= q_iso_work[e, (i + 1)]
        for e in sets["employees"]
        for i in range(len(days) - 2)
    ),
    name="isolated_working_days",
)

model.addConstrs(
    (
        gamma[e, i] - gamma[e, (i + 1)] + gamma[e, (i + 2)] - 1 <= q_iso_off[e, (i + 1)]
        for e in sets["employees"]
        for i in range(len(days) - 2)
    ),
    name="isolated_off_days",
)

model.addConstrs(
    (
        quicksum(gamma[e, i_marked] for i_marked in range(i, i + L_C_D)) - L_C_D <= q_con[e, i]
        for e in sets["employees"]
        for i in range(len(days) - L_C_D)
    ),
    name="consecutive_days",
)


model.addConstrs(
    (
        f_plus[e] - f_minus[e]
        == weights["rest"] * quicksum(v * w[e, t, v] for t, v in off_shifts)
        - weights["contracted hours"] * lam[e]
        - weights["partial weekends"] * quicksum(ro_sat[e, j] + ro_sun[e, j] for j in weeks)
        - weights["isolated working days"] * quicksum(q_iso_work[e, i] for i in days)
        - weights["isolated off days"] * quicksum(q_iso_off[e, i] for i in days)
        - weights["consecutive days"] * quicksum(q_con[e, i] for i in days)
        for e in sets["employees"]
    ),
    name="objective_function_restriction",
)
# - weights["backward rotation"] * k[e,i]
# +weights["preferences"] * quicksum(pref[e,t] for t in time_periods) * quicksum(y[c,e,t] for c in sets["competencies"])

model.addConstrs(
    (g_plus - g_minus <= f_plus[e] - f_minus[e] for e in sets["employees"]), name="lowest_fairness_score"
)
