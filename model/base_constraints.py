from gurobipy import *


class BaseConstraints:
    def __init__(self, model, var, staff, demand, competencies, time, shift_set, off_shift_set):

        self.model = model

        self.employees_with_competencies = staff["employees_with_competencies"]
        self.employees = staff["employees"]
        self.contracted_hours = staff["employee_contracted_hours"]
        self.demand = demand
        self.competencies = competencies
        self.time_periods = time["periods"][0]
        self.time_periods_per_week = time["periods"][1]
        self.days = time["days"]
        self.weeks = time["weeks"]
        self.shifts_per_day = shift_set["shifts_per_day"]
        self.shifts_overlapping_t = shift_set["shifts_overlapping_t"]
        self.off_shifts_in_week = off_shift_set["off_shifts_per_week"]
        self.t_in_off_shifts = off_shift_set["t_in_off_shifts"]
        self.off_shifts = off_shift_set["off_shifts"]
        self.time_step = time["step"]
        self.saturdays = time["saturdays"]

        self.add_minimum_demand_coverage(var.y, var.mu)
        self.add_maximum_demand_coverage(var.mu)
        self.add_deviation_from_ideal_demand(var.mu, var.delta)
        self.add_mapping_of_shift_to_demand(var.x, var.y)
        self.add_maximum_one_shift_each_day(var.x)
        self.add_helping_variable_gamma(var.x, var.gamma)
        self.add_weekly_rest(var.w)
        self.add_no_demand_cover_during_off_shift(var.w, var.y)
        self.add_contracted_hours(var.y, var.lam)

    def add_minimum_demand_coverage(self, y, mu):
        self.model.addConstrs(
            (
                quicksum(y[c, e, t] for e in self.employees_with_competencies[c])
                == self.demand["min"][c, t] + mu[c, t]
                for c in self.competencies
                for t in self.time_periods
            ),
            name="minimum_demand_coverage",
        )

    def add_maximum_demand_coverage(self, mu):
        self.model.addConstrs(
            (
                mu[c, t] <= self.demand["max"][c, t] - self.demand["min"][c, t]
                for c in self.competencies
                for t in self.time_periods
            ),
            name="mu_less_than_difference",
        )

    def add_deviation_from_ideal_demand(self, mu, delta):
        self.model.addConstrs(
            (
                mu[c, t] + self.demand["min"][c, t] - self.demand["ideal"][c, t]
                == delta["plus"][c, t] - delta["minus"][c, t]
                for t in self.time_periods
                for c in self.competencies
            ),
            name="deviation_from_ideal_demand",
        )

    def add_maximum_one_shift_each_day(self, x):
        self.model.addConstrs(
            (
                quicksum(x[e, t, v] for t, v in self.shifts_per_day[i]) <= 1
                for e in self.employees
                for i in self.days
            ),
            name="cover_maximum_one_shift",
        )

    def add_mapping_of_shift_to_demand(self, x, y):

        self.model.addConstrs(
            (
                quicksum(x[e, t_marked, v] for t_marked, v in self.shifts_overlapping_t[t])
                == quicksum(y[c, e, t] for c in self.competencies)
                for e in self.employees
                for t in self.time_periods
            ),
            name="mapping_shift_to_demand",
        )

    def add_max_one_demand_cover_each_time(self, y):
        self.model.addConstrs(
            (
                quicksum(y[c, e, t] for c in self.competencies) <= 1
                for e in self.employees
                for t in self.time_periods
            ),
            name="only_cover_one_demand_at_a_time",
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

    def add_weekly_rest(self, w):
        self.model.addConstrs(
            (
                quicksum(w[e, t, v] for t, v in self.off_shifts_in_week[j]) == 1
                for e in self.employees
                for j in self.weeks
            ),
            name="one_weekly_off_shift_per_week",
        )

    def add_no_demand_cover_during_off_shift(self, w, y):
        self.model.addConstrs(
            (
                len(self.t_in_off_shifts[t, v]) * w[e, t, v]
                <= quicksum(
                    quicksum((1 - y[c, e, t_mark]) for c in self.competencies)
                    for t_mark in self.t_in_off_shifts[t, v]
                )
                for e in self.employees
                for t, v in self.off_shifts
            ),
            name="no_work_during_off_shift",
        )

    def add_contracted_hours(self, y, lam):
        self.model.addConstrs(
            (
                quicksum(
                    quicksum(self.time_step * y[c, e, t] for t in self.time_periods)
                    for c in self.competencies
                )
                + lam[e]
                == len(self.weeks) * self.contracted_hours[e]
                for e in self.employees
            ),
            name="contracted_hours",
        )
