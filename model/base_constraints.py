from gurobipy import *


class BaseConstraints:
    def __init__(self, model, sets, var):

        self.model = model

        self.add_minimum_demand_coverage(sets, var["y"], var["mu"])
        self.add_maximum_demand_coverage(sets, var["mu"])
        self.add_deviation_from_ideal_demand(sets, var["mu"], var["delta"])
        self.add_mapping_of_shift_to_demand(sets, var["x"], var["y"])
        self.add_maximum_one_shift_each_day(sets, var["x"])
        self.add_calculate_helping_variable_gamma(sets, var["x"], var["gamma"])
        self.add_weekly_rest(sets, var["w"])
        self.add_no_demand_cover_during_off_shift(sets, var["w"], var["x"], var["y"])
        self.add_contracted_hours(sets, var["y"], var["lam"])

    def add_minimum_demand_coverage(self, sets, y, mu):
        self.model.addConstrs(
            (
                quicksum(y[c, e, t] for e in sets["employees"]["competencies"][c])
                == sets["demand"]["min"][c, t] + mu[c, t]
                for c in sets["competencies"]
                for t in sets["time"]["periods"]
            ),
            name="minimum_demand_coverage",
        )

    def add_maximum_demand_coverage(self, sets, mu):
        self.model.addConstrs(
            (
                mu[c, t] <= sets["demand"]["max"][c, t] - sets["demand"]["min"][c, t]
                for c in sets["competencies"]
                for t in sets["time"]["periods"]
            ),
            name="mu_less_than_difference",
        )

    def add_deviation_from_ideal_demand(self, sets, mu, delta):
        self.model.addConstrs(
            (
                mu[c, t] + sets["demand"]["min"][c, t] - sets["demand"]["ideal"][c, t]
                == delta["plus"][c, t] - delta["minus"][c, t]
                for t in sets["time"]["periods"]
                for c in sets["competencies"]
            ),
            name="deviation_from_ideal_demand",
        )

    def add_maximum_one_shift_each_day(self, sets, x):
        self.model.addConstrs(
            (
                quicksum(x[e, t, v] for t, v in sets["shifts"]["day"][i]) <= 1
                for e in sets["employees"]["all"]
                for i in sets["time"]["days"]
            ),
            name="cover_maximum_one_shift",
        )

    def add_mapping_of_shift_to_demand(self, sets, x, y):
        self.model.addConstrs(
            (
                quicksum(
                    x[e, t_marked, v] for t_marked, v in sets["time"]["shifts_overlapping_t"][t]
                )
                == quicksum(y[c, e, t] for c in sets["competencies"])
                for e in sets["employees"]["all"]
                for t in sets["time"]["periods"]
            ),
            name="mapping_shift_to_demand",
        )

    def add_max_one_demand_cover_each_time(self, sets, y):
        self.model.addConstrs(
            (
                quicksum(y[c, e, t] for c in sets["competencies"]) <= 1
                for e in sets["employees"]
                for t in sets["time_periods"]
            ),
            name="only_cover_one_demand_at_a_time",
        )

    def add_calculate_helping_variable_gamma(self, sets, x, gamma):
        self.model.addConstrs(
            (
                quicksum(x[e, t, v] for t, v in sets["shifts"]["day"][i]) == gamma[e, i]
                for e in sets["employees"]["all"]
                for i in sets["time"]["days"]
            ),
            name="if_employee_e_works_day_i",
        )

    def add_weekly_rest(self, sets, w):
        self.model.addConstrs(
            (
                quicksum(w[e, t, v] for t, v in sets["shifts"]["off_shift_in_week"][j]) == 1
                for e in sets["employees"]["all"]
                for j in sets["time"]["weeks"]
            ),
            name="one_weekly_off_shift_per_week",
        )

    def add_no_demand_cover_during_off_shift(self, model, sets, w, x, y):
        self.model.addConstrs(
            (
                len(sets["time"]["t_in_off_shifts"][t, v]) * w[e, t, v]
                <= quicksum(
                    quicksum((1 - y[c, e, t_mark]) for c in sets["competencies"])
                    for t_mark in sets["time"]["t_in_off_shifts"][t, v]
                )
                for e in sets["employees"]["all"]
                for t, v in sets["shifts"]["off_shifts"]
            ),
            name="no_work_during_off_shift",
        )

        # todo: fix this before merging! -Even, 5. March
        # Alternativ 2 til off_shift restriksjon (restriksjon 1.10). Virker raskere
        # model.addConstrs(
        #    (
        #        len(shifts_covered_by_off_shift[t, v]) * w[e, t, v]
        #        <= quicksum(
        #            quicksum((1 - x[e, t_marked, v_marked]) for c in sets["competencies"])
        #            for t_marked, v_marked in shifts_covered_by_off_shift[t, v]
        #        )
        #        for e in sets["employees"]
        #        for t, v in sets["shifts"]["off_shifts"]
        #    ),
        #    name="no_work_during_off_shift",
        # )

    def add_contracted_hours(self, sets, y, lam):
        self.model.addConstrs(
            (
                quicksum(
                    quicksum(sets["time"]["step"] * y[c, e, t] for t in sets["time"]["periods"])
                    for c in sets["competencies"]
                )
                + lam[e]
                == len(sets["time"]["weeks"]) * sets["employees"]["contracted_hours"][e]
                for e in sets["employees"]["all"]
            ),
            name="contracted_hours",
        )
