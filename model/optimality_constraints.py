from gurobipy import *

from model.base_constraints import BaseConstraints


class OptimalityConstraints(BaseConstraints):

    def __init__(self, model, sets, var):

        super(OptimalityConstraints, self).__init__(model, sets, var)

        self.add_minimum_weekly_work_hours(sets, var["y"])
        self.add_maximum_weekly_work_hours(sets, var["y"])
        self.add_partial_weekends(sets, var["gamma"], var["rho"])
        self.add_isolated_working_days(sets, var["gamma"], var["q"])
        self.add_isolated_off_days(sets, var["gamma"], var["q"])
        self.add_consecutive_days(sets, var["gamma"], var["q"])

    def add_minimum_weekly_work_hours(self, sets, y):

        self.model.addConstrs(
            (
                quicksum(
                    quicksum(
                        sets["time"]["step"] * y[c, e, t]
                        for t in sets["time"]["periods_in_week"][j]
                    )
                    for c in sets["competencies"]
                )
                >= 0.1 * sets["employees"]["contracted_hours"][e]
                for e in sets["employees"]["all"]
                for j in sets["time"]["weeks"]
            ),
            name="min_weekly_work_hours",
        )

    def add_maximum_weekly_work_hours(self, sets, y):
        self.model.addConstrs(
            (
                quicksum(
                    quicksum(
                        sets["time"]["step"] * y[c, e, t]
                        for t in sets["time"]["periods_in_week"][j]
                    )
                    for c in sets["competencies"]
                )
                <= 1.4 * sets["employees"]["contracted_hours"][e]
                for e in sets["employees"]["all"]
                for j in sets["time"]["weeks"]
            ),
            name="maximum_weekly_work_hours",
        )

    def add_partial_weekends(self, sets, gamma, rho):
        self.model.addConstrs(
            (
                gamma[e, i] - gamma[e, (i + 1)] == rho["sat"][e, i] - rho["sun"][e, (i + 1)]
                for e in sets["employees"]["all"]
                for i in sets["time"]["saturdays"]
            ),
            name="partial_weekends",
        )

    def add_isolated_working_days(self, sets, gamma, q):
        self.model.addConstrs(
            (
                -gamma[e, i] + gamma[e, (i + 1)] - gamma[e, (i + 2)] <= q["iso_work"][e, (i + 1)]
                for e in sets["employees"]["all"]
                for i in range(len(sets["time"]["days"]) - 2)
            ),
            name="isolated_working_days",
        )

    def add_isolated_off_days(self, sets, gamma, q):
        self.model.addConstrs(
            (
                gamma[e, i] - gamma[e, (i + 1)] + gamma[e, (i + 2)] - 1 <= q["iso_off"][e, (i + 1)]
                for e in sets["employees"]["all"]
                for i in range(len(sets["time"]["days"]) - 2)
            ),
            name="isolated_off_days",
        )

    def add_consecutive_days(self, sets, gamma, q):
        self.model.addConstrs(
            (
                quicksum(
                    gamma[e, i_marked]
                    for i_marked in range(i, i + sets["limit_for_consecutive_days"])
                )
                - sets["limit_for_consecutive_days"]
                <= q["con"][e, i]
                for e in sets["employees"]["all"]
                for i in range(len(sets["days"]) - sets["limit_for_consecutive_days"])
            ),
            name="consecutive_days",
        )
