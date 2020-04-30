from gurobipy import *


class BaseConstraints:
    def __init__(
        self, model, var, competencies, staff, demand, time_set, shifts_set, off_shifts_set
    ):

        self.model = model

        self.competencies = competencies

        self.employees = staff["employees"]
        self.employees_with_competencies = staff["employees_with_competencies"]
        self.contracted_hours = staff["employee_contracted_hours"]

        self.demand = demand

        self.time_step = time_set["step"]
        self.time_periods = time_set["periods"][0]
        self.time_periods_per_week = time_set["periods"][1]
        self.days = time_set["days"]
        self.weeks = time_set["weeks"]
        self.saturdays = time_set["saturdays"]

        self.shifts_per_day = shifts_set["shifts_per_day"]
        self.shifts_overlapping_t = shifts_set["shifts_overlapping_t"]
        self.shifts_covered_by_off_shift = shifts_set["shifts_covered_by_off_shift"]
        self.off_shifts_in_week = off_shifts_set["off_shifts_per_week"]
        self.t_in_off_shifts = off_shifts_set["t_in_off_shifts"]
        self.off_shifts = off_shifts_set["off_shifts"]
        self.shifts_combinations_violating_daily_rest = shifts_set[
            "shifts_combinations_violating_daily_rest"
        ]
        self.invalid_shifts = shifts_set["invalid_shifts"]

        # Adding constraints
        self.add_minimum_demand_coverage(var.y, var.mu)
        self.add_maximum_demand_coverage(var.mu)
        self.add_deviation_from_ideal_demand(var.mu, var.delta)
        self.add_mapping_of_shift_to_demand(var.x, var.y)
        self.add_maximum_one_shift_each_day(var.x)
        self.add_weekly_rest(var.w)
        self.add_no_demand_cover_during_off_shift(var.w, var.x, var.y, version="original")
        self.add_contracted_hours(var.y, var.lam)

        for e in self.employees:
            self.add_daily_rest_shift_combinations(var.x, e)
        self.add_daily_rest_invalid_shifts(var.x)
        
    # Constraint definitions
    def add_minimum_demand_coverage(self, y, mu):
        self.model.addConstrs(
            (
                quicksum(y[c, e, t] for e in self.employees_with_competencies[c])
                == self.demand["min"][c, t] + mu[c, t]
                for c in self.competencies
                for t in self.time_periods[c]
            ),
            name="minimum_demand_coverage",
        )

    def add_maximum_demand_coverage(self, mu):
        self.model.addConstrs(
            (
                mu[c, t] <= self.demand["max"][c, t] - self.demand["min"][c, t]
                for c in self.competencies
                for t in self.time_periods[c]
            ),
            name="mu_less_than_difference",
        )

    def add_deviation_from_ideal_demand(self, mu, delta):
        self.model.addConstrs(
            (
                mu[c, t] + self.demand["min"][c, t] - self.demand["ideal"][c, t]
                == delta["plus"][c, t] - delta["minus"][c, t]
                for c in self.competencies
                for t in self.time_periods[c]
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
                == quicksum(y[c, e, t] for c in self.competencies if y.get((c,e,t)))
                for e in self.employees
                for c in self.competencies
                for t in self.time_periods[c]
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

    def add_weekly_rest(self, w):
        self.model.addConstrs(
            (
                quicksum(w[e, t, v] for t, v in self.off_shifts_in_week[j]) == 1
                for e in self.employees
                for j in self.weeks
            ),
            name="one_weekly_off_shift_per_week",
        )

    def add_no_demand_cover_during_off_shift(self, w, x, y, version):

        if version == "original":
            return self.add_no_demand_cover_during_off_shift_original(w, y)
        elif version == "alternative":
            return self.add_no_demand_cover_during_off_shift_alternative(w, x)
        else:
            raise ValueError("Unknown version of no_demand_while_off-constraint")

    def add_no_demand_cover_during_off_shift_original(self, w, y):
        self.model.addConstrs(
            (
                quicksum(len(self.t_in_off_shifts[t, v, c]) for c in self.competencies if self.t_in_off_shifts.get((t,v,c))) * w[e, t, v]
                <= quicksum(1 - y[c, e, t_mark] 
                    for c in self.competencies
                    if self.t_in_off_shifts.get((t,v,c))
                    for t_mark in self.t_in_off_shifts[t, v, c]
                )
                for e in self.employees
                for t, v in self.off_shifts
            ),
            name="no_work_during_off_shift_original",
        )

    def add_no_demand_cover_during_off_shift_alternative(self, w, x):

        self.model.addConstrs(
            (
                len(self.shifts_covered_by_off_shift[t, v]) * w[e, t, v]
                <= quicksum(
                    1 - x[e, t_marked, v_marked]
                    for t_marked, v_marked in self.shifts_covered_by_off_shift[t, v]
                )
                for e in self.employees
                for t, v in self.off_shifts
            ),
            name="no_work_during_off_shift_alternative",
        )

    def add_contracted_hours(self, y, lam):
        self.model.addConstrs(
            (
                quicksum(
                    quicksum(self.time_step * y[c, e, t] for t in self.time_periods[c])
                    for c in self.competencies
                )
                + lam[e]
                == len(self.weeks) * self.contracted_hours[e]
                for e in self.employees
            ),
            name="contracted_hours",
        )

    def add_daily_rest_shift_combinations(self, x, e):
        self.model.addConstrs(
            (
                x[e, t, v]
                + quicksum(
                    x[e, t_marked, v_marked]
                    for t_marked, v_marked in self.shifts_combinations_violating_daily_rest[e][t, v]
                )
                <= min(2, len(self.shifts_combinations_violating_daily_rest[e][t, v]))
                for t, v in self.shifts_combinations_violating_daily_rest[e]
                if len(self.shifts_combinations_violating_daily_rest[e]) > 0
            ),
            name="daily_rest_shift_combinations",
        )

    def add_daily_rest_invalid_shifts(self, x):
        self.model.addConstrs(
            (quicksum(x[e, t, v] for t, v in self.invalid_shifts[e]) == 0 for e in self.employees),
            name="invalid_shifts",
        )
