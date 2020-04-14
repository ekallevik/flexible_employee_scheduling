from random import choice, sample, choices
from heuristic.converter import set_x
from xml_loader.shift_generation import load_data, get_t_covered_by_shift, shift_lookup, get_time_periods_in_day
#from heuristic.heuristic_calculations import calculate_negative_deviation_from_demand, calculate_f
from heuristic.delta_calculations import delta_calculate_deviation_from_demand as calc_neg_dev

def add_previously_isolated_days_randomly(state, sets, destroy_set):
    employees = {i: [e for e in sets["employees"] if sum(state.x[e,t,v] for t,v in sets["shifts_at_day"][i]) == 0] for i in iso_days.keys()}
    for day, k in iso_days.items():
        delta = calculate_negative_deviation_from_demand(model, [day])
        emps = sample(employees[day], k) 
        #Needed for fully random:
        #shifts = choices(model.shifts_at_day[day], k=k)
        shifts = [sum(delta[c,t] for c in model.competencies for t in model.t_covered_by_shift[shift]) for shift in model.shifts_at_day[day]]
        shifts_sorted = sorted(shifts, reverse=True)
        shifts_2 = [model.shifts_at_day[day][shifts.index(shifts_sorted[place])] for place in range(k)]
        for e,shift in zip(emps, shifts_2):
            set_x(model, e, shift[0], shift[1], 1)
    
    
def add_previously_isolated_days_greedy(model, iso_days):
    employees = {i: [e for e in model.employees if sum(model.x[e,t,v] for t,v in model.shifts_at_day[i]) == 0] for i in iso_days.keys()}
    for i,k in iso_days.items():
        delta = calculate_negative_deviation_from_demand(model, [i])
        f = calculate_f(model, employees[i])
        f_sorted = {k: v for k, v in sorted(f.items(), key=lambda item: item[1])}
        emps = [e for e in f_sorted.keys()][:k]
        shifts = [sum(delta[c,t] for c in model.competencies for t in model.t_covered_by_shift[shift]) for shift in model.shifts_at_day[i]]
        shifts_sorted = sorted(shifts, reverse=True)
        shifts_2 = [model.shifts_at_day[i][shifts.index(shifts_sorted[place])] for place in range(k)]
        [set_x(model, e,t,v,1) for e in emps for t,v in shifts_2]


def add_random_weekends(state, sets, destroyed_set):
    print(destroyed_set.values())
    repair_set = []
    for i in destroyed_set.keys():
        emp = choice([e for e,t,v in destroyed_set[i]])
        #emp = choice([key[0] for key, value in destroyed_set.items() if value in destroyed_set[None, i]])
        t1,v1 = choice(sets["shifts_at_day"][i])
        t2,v2 = choice(sets["shifts_at_day"][i+1])
        set_x(state, sets, emp,t1,v1,1)
        set_x(state, sets, emp,t2,v2,1)
        repair_set.append((emp,t1,v1))
        repair_set.append((emp,t2,v2))
    return repair_set


def add_greedy_weekends(state, sets, destroyed_set):
    repair_set = []
    #Dette må gjøres smartere nå vi vet hvilken competency som velges
    for c in sets["competencies"]:
        for i in destroyed_set:
            for e,t,v in destroyed_set[i]:
                for t in sets["t_covered_by_shift"][t,v]:
                    state.soft_vars["negative_deviation_from_demand"][c,t] += 1

    for i in destroyed_set:
        #e = choice([e for e,t,v in destroyed_set[i]])
        employees = sample([e for e,t,v in destroyed_set[i]], int(len([e for e,t,v in destroyed_set[i]])/2))

        avail_shifts = [[], []]
        #avail_shifts[0] = [sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in sets["competencies"] for t in sets["t_covered_by_shift"][shift]) for shift in sets["shifts_at_day"][i]]
        #avail_shifts[1] = [sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in sets["competencies"] for t in sets["t_covered_by_shift"][shift]) for shift in sets["shifts_at_day"][i+1]]


        avail_shifts[0] = {shift: sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in sets["competencies"] for t in sets["t_covered_by_shift"][shift]) for shift in sets["shifts_at_day"][i]}
        avail_shifts[1] = {shift: sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in sets["competencies"] for t in sets["t_covered_by_shift"][shift]) for shift in sets["shifts_at_day"][i+1]}

        ind = [sorted(avail_shifts[0], key=avail_shifts[0].get, reverse=True)[:len(employees)], sorted(avail_shifts[1], key=avail_shifts[1].get, reverse=True)[:len(employees)]]
        
        #ind = [avail_shifts[0].index(max(avail_shifts[0])), avail_shifts[1].index(max(avail_shifts[1]))]

       # print(avail_shifts)
       # print(ind)
        if(ind[0] == 0 and ind[1] == 0):
            continue

        #t1,v1 = sets["shifts_at_day"][i][ind[0]]
        #t2,v2 = sets["shifts_at_day"][i+1][ind[1]]
        for e in range(len(employees)):
            t1, v1 = ind[0][e]
            t2, v2 = ind[1][e]
            emp = employees[e]
            #print("shift1: %s, %s. Shift2: %s, %s" % (t1, v1, t2, v2))
            set_x(state, sets, emp, t1, v1, 1)
            set_x(state, sets, emp, t2, v2, 1)

            repair_set.append((emp,t1,v1))
            repair_set.append((emp,t2,v2))

            for t in (sets["t_covered_by_shift"][t1,v1] + sets["t_covered_by_shift"][t2,v2]):
                state.soft_vars["negative_deviation_from_demand"][0,t] -= 1
    return repair_set


def lowest_contracted_hours(model, delta_c, delta):
    employee = min(delta_c, key=delta_c.get)
    working_days = []
    for i in model.days:
        if sum(model.x[employee,t,v].x for t,v in model.shifts_at_day[i]) != 0:
            working_days.append(i)
    maximum_deviation_from_demand = {}
    for i in model.days: 
        if i not in working_days:
            for shift in model.shifts_at_day[i]:
                maximum_deviation_from_demand[shift] = sum(delta[0,t] for t in model.t_covered_by_shift[shift])
    #print(maximum_deviation_from_demand)
    placement = max(maximum_deviation_from_demand, key=maximum_deviation_from_demand.get)
    #print(x[employee,placement[0], placement[1]])
    #Remember to set y when you set x values as these should always be mapped
   # print(x[employee, placement[0], placement[1]].set(1))
   # delta2 = calculate_deviation_from_contracted_hours()
   # print(employee)
   # print(min(delta2, key=delta2.get))
    