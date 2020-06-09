
from gurobipy import *

from utils.const import \
    L_WORK, M_WORK_ALLOCATION, HOURS_IN_A_DAY, HOURS_IN_A_WEEK, LIMIT_CONSECUTIVE_DAYS


class ImplicitConstraints:

    def __init__(self, model, var, data):

        self.model = model

        self.demand = data["demand"]
        self.employees = data["staff"]["employees"]
        self.employees_with_competency = data["staff"]["employees_with_competencies"]
        self.competencies = data["competencies"]
        self.time_step = data["time"]["step"]
        self.time_periods = data["time"]["periods"][0]
        self.combined_time_periods = data["time"]["combined_time_periods"][0]
        self.combined_time_periods_in_day = data["time"]["combined_time_periods"][2]
        self.time_periods_with_no_demand = data["time"]["time_periods_with_no_demand"]
        self.every_time_period = data["time"]["every_time_period"]
        self.shift_durations = data["shift_durations"]
        self.days = data["time"]["days"]
        self.weeks = data["time"]["weeks"]
        self.saturdays = data["time"]["saturdays"]
        self.daily_offset = data["staff"]["employee_daily_offset"]
        self.daily_rest = data["staff"]["employee_daily_rest"]
        self.weekly_offset = data["staff"]["employee_weekly_offset"]
        self.weekly_rest = data["staff"]["employee_with_weekly_rest"]
        self.contracted_hours = data["staff"]["employee_contracted_hours"]

        # Adding constraints
        #self.add_no_shift_while_no_demand(var.x)
        self.add_minimum_demand_coverage(var.y, var.mu)
        self.add_maximum_demand_coverage(var.mu)
        self.add_deviation_from_ideal_demand(var.mu, var.delta)
        self.add_mapping_shift_to_demand(var.x, var.y)
        self.add_max_one_demand_cover_each_time(var.y)
        self.add_maximum_one_daily_shift(var.x)
        self.add_no_demand_cover_while_off_shift(var.y, var.w_day, var.w_week)
        self.add_allocate_to_work_when_covering_demand(var.y, var.gamma)
        self.add_minimum_daily_rest(var.w_day)
        self.add_minimum_weekly_rest(var.w_week)
        self.add_contracted_hours(var.y, var.lam)
        self.add_partial_weekends(var.gamma, var.rho)
        self.add_isolated_working_days(var.gamma, var.q)
        self.add_isolated_off_days(var.gamma, var.q)
        self.add_consecutive_days(var.gamma, var.q)

    def add_no_shift_while_no_demand(self, x):

        self.model.addConstrs(
            (
                quicksum(
                    quicksum(
                        x[e, t_marked, v] for t_marked in self.combined_time_periods
                        if t_marked + v - self.time_step in self.time_periods_with_no_demand
                    )
                    for v in self.shift_durations["work"]
                ) == 0
                for e in self.employees
            ),
            name="no_work_shift_ending_in_no_demand_allowed"
        )

    def add_minimum_demand_coverage(self, y, mu):

        self.model.addConstrs(
            (
                quicksum(y[c, e, t] for e in self.employees_with_competency[c])
                == self.demand["min"][c, t] + mu[c, t]
                for c in self.competencies
                for t in self.time_periods[c]
            ),
            name='minimum_demand_coverage'
        )

    def add_maximum_demand_coverage(self, mu):

        self.model.addConstrs(
            (
                mu[c, t] <= self.demand["max"][c, t] - self.demand["min"][c, t]
                for c in self.competencies
                for t in self.time_periods[c]
            ),
            name='mu_less_than_difference'
        )

    def add_deviation_from_ideal_demand(self, mu, delta):

        self.model.addConstrs(
            (
                mu[c, t] + self.demand["min"][c, t] - self.demand["ideal"][c, t]
                == delta["plus"][c, t] - delta["minus"][c, t]
                for c in self.competencies
                for t in self.time_periods[c]
            ),
            name="deviation_from_ideal_demand"
        )

    def add_mapping_shift_to_demand(self, x, y):

        self.model.addConstrs(
            (
                quicksum(
                    quicksum(
                        x[e, t_marked, v] for t_marked in self.combined_time_periods
                        if t - v + self.time_step <= t_marked <= t
                    )
                    for v in self.shift_durations["work"]
                )
                == quicksum(y[c, e, t] for c in self.competencies if y.get((c, e, t)))
                for e in self.employees
                for t in self.combined_time_periods
            ),
            name="mapping_shift_to_demand"
        )

    def add_max_one_demand_cover_each_time(self, y):

        self.model.addConstrs(
            (
                quicksum(
                    y[c, e, t] for c in self.competencies if y.get((c, e, t))
                ) <= 1
                for e in self.employees
                for t in self.combined_time_periods
            ),
            name='max_one_demand_per_time_period'
        )

    def add_maximum_one_daily_shift(self, x):

        self.model.addConstrs(
            (
                quicksum(
                    quicksum(
                        x[e, t, v] for t in self.combined_time_periods_in_day[day]
                        )
                    for v in self.shift_durations["work"]
                ) <= 1
                for day in self.days
                for e in self.employees
            ),
            name="maximum_one_daily_shift"
        )

    def add_no_demand_cover_while_off_shift(self, y, w_day, w_week):

        self.model.addConstrs(
            (
                self.time_step *
                quicksum(
                    (1 - quicksum(y[c, e, t_marked] for c in self.competencies if y.get((c, e, t_marked))))
                    for t_marked in self.combined_time_periods
                    if t <= t_marked <= t + v - self.time_step
                    )
                >= quicksum(
                    self.time_step for t_marked_2 in self.combined_time_periods
                    if t <= t_marked_2 <= t + v - self.time_step
                )
                * w_day[e, t, v]
                for e in self.employees
                for v in self.shift_durations["daily_off"]
                for t in self.combined_time_periods if t + v - self.time_step <= max(self.combined_time_periods)
            ),
            name="cover_no_demand_while_daily_off_shift"
        )

        self.model.addConstrs(
            (
                self.time_step *
                quicksum(
                    (1 - quicksum(y[c, e, t_marked] for c in self.competencies if y.get((c, e, t_marked))))
                    for t_marked in self.combined_time_periods
                    if t <= t_marked <= t + v - self.time_step
                )
                >= quicksum(
                    self.time_step for t_marked_2 in self.combined_time_periods
                    if t <= t_marked_2 <= t + v - self.time_step
                )
                * w_week[e, t, v]
                for e in self.employees
                for v in self.shift_durations["weekly_off"]
                for t in self.combined_time_periods if t + v - self.time_step <= max(self.combined_time_periods)
            ),
            name="cover_no_demand_while_weekly_off_shift"
        )

    def add_allocate_to_work_when_covering_demand(self, y, gamma):

        self.model.addConstrs(
            (
                self.time_step *
                quicksum(
                    quicksum(
                        y[c, e, t] for c in self.competencies if y.get((c, e, t))
                    )
                    for t in self.combined_time_periods_in_day[i]
                )
                - L_WORK
                <= M_WORK_ALLOCATION * gamma[e, i]
                for e in self.employees
                for i in self.days
            ),
            name='allocated_to_work_1'
        )

        self.model.addConstrs(
            (
                self.time_step *
                quicksum(
                    quicksum(
                        y[c, e, t] for c in self.competencies if y.get((c, e, t))
                    )
                    for t in self.combined_time_periods_in_day[i]
                )
                - L_WORK
                >= M_WORK_ALLOCATION * (gamma[e, i] - 1) + self.time_step
                for e in self.employees
                for i in self.days
            ),
            name='allocated_to_work_2'
        )

    def add_minimum_daily_rest(self, w_day):

        self.model.addConstrs(
            (
                quicksum(
                    quicksum(
                        w_day[e, t, v] for t in self.every_time_period
                        if self.daily_offset[e] + (i + 1) * HOURS_IN_A_DAY - v
                        >= t >= self.daily_offset[e] + i * HOURS_IN_A_DAY
                    )
                    for v in self.shift_durations["daily_off"] if v == self.daily_rest[e]
                )
                == 1
                for e in self.employees
                for i in self.days
            ),
            name='minimum_daily_rest'
        )

    def add_minimum_weekly_rest(self, w_week):

        self.model.addConstrs(
            (
                quicksum(
                    quicksum(
                        w_week[e, t, v] for t in self.every_time_period
                        if self.weekly_offset[e] + (j + 1) * HOURS_IN_A_WEEK - v
                        >= t >= self.weekly_offset[e] + j * HOURS_IN_A_WEEK
                    )
                    for v in self.shift_durations["weekly_off"]
                    if v >= self.weekly_rest[e]
                )
                == 1
                for e in self.employees
                for j in self.weeks
            ),
            name="minimum_weekly_rest"
        )

        self.model.addConstrs(
            (
                quicksum(
                    quicksum(
                        w_week[e, t, v] for t in self.every_time_period
                        if self.weekly_offset[e] + (j + 1) * HOURS_IN_A_WEEK
                        >= t > self.weekly_offset[e] + (j + 1) * HOURS_IN_A_WEEK - v
                    )
                    for v in self.shift_durations["weekly_off"] if v >= self.weekly_rest[e]
                )
                == 0
                for e in self.employees
                for j in self.weeks
            ),
            name="not_allocating_invalid_weekly_rest"
        )

    def add_contracted_hours(self, y, lam):

        self.model.addConstrs(
            (
                quicksum(
                    quicksum(
                        self.time_step * y[c, e, t] for c in self.competencies if y.get((c, e, t))
                    )
                    for t in self.combined_time_periods
                )
                + lam[e]
                == len(self.weeks) * self.contracted_hours[e]
                for e in self.employees
            ),
            name="less_than_contracted_hours"
        )

    def add_partial_weekends(self, gamma, rho):
        self.model.addConstrs(
            (
                gamma[e, i] - gamma[e, (i + 1)]
                == rho["sat"][e, i] - rho["sun"][e, (i + 1)]
                for e in self.employees
                for i in self.saturdays
            ),
            name="partial_weekends"
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

        self.model.addConstrs(
            (
                quicksum(
                    gamma[e, i_marked] for i_marked in self.get_consecutive_days_time_window(i)
                )
                - LIMIT_CONSECUTIVE_DAYS
                <= q["con"][e, i] - 1
                for e in self.employees
                for i in range(len(self.days) - LIMIT_CONSECUTIVE_DAYS)
            ),
            name="consecutive_days",
        )

    def get_consecutive_days_time_window(self, day):

        return range(day, day + LIMIT_CONSECUTIVE_DAYS)
