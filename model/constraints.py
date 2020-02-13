from gurobipy import *


# todo: convert min_demand to tupledict
# todo: add competencies
def add_minimum_demand(model, y, employees, min_demand, mu, competencies, time_periods):
    model.addConstrs((
        quicksum(y[c, e, t] for e in employees)
        ==
        min_demand[c][t] + mu[c, t]
        for c in competencies
        for t in time_periods),
        name='minimum_demand_coverage')


def add_maximum_demand(model, max_demand, min_demand, mu, competencies, time_periods):
    model.addConstrs((
        mu[c, t]
        <=
        max_demand[c][t] - min_demand[c][t]
        for c in competencies
        for t in time_periods),
        name="maximum_demand_coverage"
    )


def add_deviation_from_ideal_demand(model, min_demand, ideal_demand, mu, delta_plus, delta_minus,
                                    competencies, time_periods):
    model.addConstrs((
        mu[c, t] + min_demand[c][t] - ideal_demand[c][t]
        ==
        delta_plus[c, t] - delta_minus[c, t]
        for c in competencies
        for t in time_periods),
        name="deviation_from_ideal_demand")


def add_maximum_one_allocation_for_each_time(model, competencies, employees, time_periods, y):
    model.addConstrs((
        quicksum(y[c, e, t] for c in competencies)
        <=
        1
        for e in employees
        for t in time_periods),
        name="maximum_one_y_for_each_time"
    )


def add_maximum_one_shift_for_each_day(model, employees, days, shifts, x):
    model.addConstrs((
        quicksum(x[e, i, s] for s in shifts)
        <=
        1
        for e in employees
        for i in days
    ))


def add_mapping_of_shift_to_demand(model, employees, days, shifts, competencies, time_periods, x, y):
    model.addConstrs((
        quicksum(x[e, i, s] for s in shifts)
        ==
        quicksum(y[c, e, t] for c in competencies)
        for e in employees
        for i in days
        for t in time_periods),
        name="mapping_of_shift_to_demand"
    )


def add_mapping_of_off_shift_to_rest(model, employees, days, off_shifts, competencies, time_periods, w, y):
    model.addConstrs((
        quicksum(w[e, i, q] for q in off_shifts)
        ==
        quicksum(1 - y[c, e, t] for c in competencies)
        for e in employees
        for i in days
        for t in time_periods),
        name="mapping_off_of_shift_to_rest"
    )

    raise NotImplementedError("This constraint is not necessary with explicit shifts")


def add_minimum_daily_rest():
    raise NotImplementedError("This constraint is not necessary with explicit shifts")


# TODO: must implement this constraint for weeks and not planning period
def add_minimum_weekly_rest(model, employees, days_in_week, weeks, off_shifts, w):
    model.addConstrs((
        quicksum(w[e, i, q] for j in weeks for i in days_in_week[j])
        ==
        1
        for e in employees
        for q in off_shifts),
        name="minimum_weekly_rest"
    )


def add_maximum_contracted_hours(model, competencies, employees, time_periods, number_of_weeks,
                                 contracted_hours, y, lambda_var):
    model.addConstrs((
        quicksum(
            quicksum(y[c, e, t] for t in time_periods)
            for c in competencies
        ) + lambda_var[e]
        ==
        number_of_weeks * contracted_hours[e]
        for e in employees),
        name="maximum_contracted_hours"
    )
