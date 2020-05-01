from gurobipy import *

from model.base_constraints import BaseConstraints


class OptimalityConstraints(BaseConstraints):
    def __init__(
        self,
        model,
        var,
        staff,
        demand,
        competencies,
        time_set,
        shifts_set,
        off_shifts_set,
        limit_on_consecutive_days,
    ):

        super(OptimalityConstraints, self).__init__(
            model=model,
            var=var,
            staff=staff,
            demand=demand,
            competencies=competencies,
            time_set=time_set,
            shifts_set=shifts_set,
            off_shifts_set=off_shifts_set,
        )

        self.limit_on_consecutive_days = limit_on_consecutive_days

        self.add_minimum_weekly_work_hours(var.y)
        self.add_maximum_weekly_work_hours(var.y)
        self.add_partial_weekends(var.gamma, var.rho)
        self.add_isolated_working_days(var.gamma, var.q)
        self.add_isolated_off_days(var.gamma, var.q)
        self.add_consecutive_days(var.gamma, var.q)
        self.add_helping_variable_gamma(var.x, var.gamma)

    def add_minimum_weekly_work_hours(self, y):

        self.model.addConstrs(
            (
                quicksum(
                    quicksum(self.time_step * y[c, e, t] for t in self.time_periods_per_week[j])
                    for c in self.competencies
                )
                >= 0.1 * self.contracted_hours[e]
                for e in self.employees
                for j in self.weeks
            ),
            name="min_weekly_work_hours",
        )

    def add_maximum_weekly_work_hours(self, y):
        self.model.addConstrs(
            (
                quicksum(
                    quicksum(self.time_step * y[c, e, t] for t in self.time_periods_per_week[j])
                    for c in self.competencies
                )
                <= 1.4 * self.contracted_hours[e]
                for e in self.employees
                for j in self.weeks
            ),
            name="maximum_weekly_work_hours",
        )

    def add_partial_weekends(self, gamma, rho):

        self.model.addConstrs(
            (
                gamma[e, i] - gamma[e, i + 1] == rho["sat"][e, i] - rho["sun"][e, i + 1]
                for e in self.employees
                for i in self.saturdays
            ),
            name="partial_weekends",
        )

    def add_isolated_working_days(self, gamma, q):
        self.model.addConstrs(
            (
                -gamma[e, i] + gamma[e, (i + 1)] - gamma[e, (i + 2)] <= q["iso_work"][e, (i + 1)]
                for e in self.employees
                for i in range(len(self.days) - 2)
            ),
            name="isolated_working_days",
        )

    def add_isolated_off_days(self, gamma, q):
        self.model.addConstrs(
            (
                gamma[e, i] - gamma[e, (i + 1)] + gamma[e, (i + 2)] - 1 <= q["iso_off"][e, (i + 1)]
                for e in self.employees
                for i in range(len(self.days) - 2)
            ),
            name="isolated_off_days",
        )

    def add_consecutive_days(self, gamma, q):
        return self.model.addConstrs(
            (
                quicksum(
                    gamma[e, i_marked] for i_marked in self.get_consecutive_days_time_window(i)
                )
                - self.limit_on_consecutive_days
                <= q["con"][e, i] - 1
                for e in self.employees
                for i in range(len(self.days) - self.limit_on_consecutive_days)
            ),
            name="consecutive_days",
        )

    def add_helping_variable_gamma(self, x, gamma):
        self.model.addConstrs(
            (
                quicksum(x[e, t, v] for t, v in self.shifts_per_day[i]) == gamma[e, i]
                for e in self.employees
                for i in self.days
            ),
            name="if_employee_e_works_day_i",
        )

    def get_consecutive_days_time_window(self, day):
        return range(day, day + self.limit_on_consecutive_days)
