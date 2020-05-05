from random import choice, choices, sample

from converter import set_x
from heuristic_calculations import calculate_f, calculate_negative_deviation_from_demand


def add_previously_isolated_days_randomly(model, iso_days):
    employees = {
        i: [
            e
            for e in model.employees
            if sum(model.x[e, t, v] for t, v in model.shifts_at_day[i]) == 0
        ]
        for i in iso_days.keys()
    }
    for day, k in iso_days.items():
        delta = calculate_negative_deviation_from_demand(model, [day])
        emps = sample(employees[day], k)
        # An alternative implementation. It is a totally random implementation instead of a semi-random
        # implementation as used otherwise. The lines 15-17 would have to be commented out.
        # shifts = choices(model.shifts_at_day[day], k=k)
        shifts = [
            sum(delta[c, t] for c in model.competencies for t in model.t_covered_by_shift[shift])
            for shift in model.shifts_at_day[day]
        ]
        shifts_sorted = sorted(shifts, reverse=True)
        shifts_2 = [
            model.shifts_at_day[day][shifts.index(shifts_sorted[place])] for place in range(k)
        ]
        for e, shift in zip(emps, shifts_2):
            set_x(model, e, shift[0], shift[1], 1)


def add_previously_isolated_days_greedy(model, iso_days):
    employees = {
        i: [
            e
            for e in model.employees
            if sum(model.x[e, t, v] for t, v in model.shifts_at_day[i]) == 0
        ]
        for i in iso_days.keys()
    }
    for i, k in iso_days.items():
        delta = calculate_negative_deviation_from_demand(model, [i])
        f = calculate_f(model, employees[i])
        f_sorted = {k: v for k, v in sorted(f.items(), key=lambda item: item[1])}
        emps = [e for e in f_sorted.keys()][:k]
        shifts = [
            sum(delta[c, t] for c in model.competencies for t in model.t_covered_by_shift[shift])
            for shift in model.shifts_at_day[i]
        ]
        shifts_sorted = sorted(shifts, reverse=True)
        shifts_2 = [
            model.shifts_at_day[i][shifts.index(shifts_sorted[place])] for place in range(k)
        ]
        [set_x(model, e, t, v, 1) for e in emps for t, v in shifts_2]


def add_random_weekends(model, partial):
    actual_partial_weekends = [key for key, value in partial[0].items() if value != 0]
    for e, i in actual_partial_weekends:
        t1, v1 = choice(model.shifts_at_day[i])
        t2, v2 = choice(model.shifts_at_day[i + 1])
        set_x(model, e, t1, v1, 1)
        set_x(model, e, t2, v2, 1)


def add_greedy_weekends(model, partial):
    actual_partial_weekends = [key for key, value in partial[0].items() if value != 0]
    for e, i in actual_partial_weekends:
        delta = calculate_negative_deviation_from_demand(model)
        avail_shifts = [[], []]
        avail_shifts[0] = [
            sum(delta[c, t] for c in model.competencies for t in model.t_covered_by_shift[shift])
            for shift in model.shifts_at_day[i]
        ]
        avail_shifts[1] = [
            sum(delta[c, t] for c in model.competencies for t in model.t_covered_by_shift[shift])
            for shift in model.shifts_at_day[i + 1]
        ]
        ind = [
            avail_shifts[0].index(max(avail_shifts[0])),
            avail_shifts[1].index(max(avail_shifts[1])),
        ]
        if ind[0] == 0 and ind[1] == 0:
            continue

        t1, v1 = model.shifts_at_day[i][ind[0]]
        t2, v2 = model.shifts_at_day[i + 1][ind[1]]
        set_x(model, e, t1, v1, 1)
        set_x(model, e, t2, v2, 1)


def lowest_contracted_hours(model, delta_c, delta):
    employee = min(delta_c, key=delta_c.get)
    working_days = []
    for i in model.days:
        if sum(model.x[employee, t, v].x for t, v in model.shifts_at_day[i]) != 0:
            working_days.append(i)
    maximum_deviation_from_demand = {}
    for i in model.days:
        if i not in working_days:
            for shift in model.shifts_at_day[i]:
                maximum_deviation_from_demand[shift] = sum(
                    delta[0, t] for t in model.t_covered_by_shift[shift]
                )
    # print(maximum_deviation_from_demand)
    placement = max(maximum_deviation_from_demand, key=maximum_deviation_from_demand.get)
    # print(x[employee,placement[0], placement[1]])
    # Remember to set y when you set x values as these should always be mapped


# print(x[employee, placement[0], placement[1]].set(1))
# delta2 = calculate_deviation_from_contracted_hours()
# print(employee)
# print(min(delta2, key=delta2.get))
