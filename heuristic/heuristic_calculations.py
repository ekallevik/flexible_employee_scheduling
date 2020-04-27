from collections import defaultdict
from operator import itemgetter

def calculate_deviation_from_demand(model, y):
    delta = {}
    for c in model.competencies:
        for t in model.time_periods:
            delta[c,t] = (sum(y[c,e,t] for e in model.employee_with_competencies[c]) - model.demand["ideal"][c,t])
            # if(delta[c,t] - abs(model.delta["plus"][c,t].x - model.delta["minus"][c,t].x)) != 0:
            #     print(delta[c,t] - abs(model.delta["plus"][c,t].x - model.delta["minus"][c,t].x))
            #     print("Different Delta")
    return delta

def calculate_weekly_rest(model, x, w):
    actual_shifts = {(e, j): [(t,v) for t,v in model.shifts_at_week[j] if x[e,t,v] == 1] for e in model.employees for j in model.weeks}
    off_shift_periods = defaultdict(list)
    important = [7*24*i for i in range(len(model.weeks)+1)]
    for key in actual_shifts.keys():
        week = int(key[1])
        if(actual_shifts[key][0][0] - important[week] >= 36):
            off_shift_periods[key].append((important[week], actual_shifts[key][0][0] - important[week]))

        if(important[week + 1] - (actual_shifts[key][-1][0] + actual_shifts[key][-1][1]) >= 36):
            off_shift_periods[key].append(((actual_shifts[key][-1][0] + actual_shifts[key][-1][1]), important[week + 1] - (actual_shifts[key][-1][0] + actual_shifts[key][-1][1])))

        for i in range(len(actual_shifts[key])-1):
            if(actual_shifts[key][i+1][0] - (actual_shifts[key][i][0] + actual_shifts[key][i][1]) >= 36):
                off_shift_periods[key].append(((actual_shifts[key][i][0] + actual_shifts[key][i][1]), actual_shifts[key][i+1][0] - (actual_shifts[key][i][0] + actual_shifts[key][i][1])))

    for key in off_shift_periods:
        w[key] = max(off_shift_periods[key],key=itemgetter(1))



def calculate_negative_deviation_from_demand(model, y):
    delta = {}
    for c in model.competencies:
        for i in model.days:
            for t in model.time_periods_in_day[i]:
                delta[c,t] = max(0, model.demand["ideal"][c,t] - sum(y[c,e,t] for e in model.employee_with_competencies[c]))
                # if(delta[c,t] - abs(model.delta["plus"][c,t].x - model.delta["minus"][c,t].x)) != 0:
                #     print(delta[c,t] - abs(model.delta["plus"][c,t].x - model.delta["minus"][c,t].x))
                #     print("Different Delta")
    return delta

def calculate_negative_deviation_from_contracted_hours(model, y):
    delta_negative_contracted_hours = {}
    for e in model.employees:
        for j in model.weeks:
            delta_negative_contracted_hours[e,j] = (model.contracted_hours[e]
            - sum(model.time_step * y[c,e,t] 
            for t in model.time_periods_in_week[j]
            for c in model.competencies))
    return delta_negative_contracted_hours

def calculate_partial_weekends(model, x):
    partial_weekend = {}
    partial_weekend_shifts = []
    for i in model.saturdays:
        for e in model.employees:
            #if(abs(sum(model.x[e,t,v] for t,v in model.shifts_at_day[i]) - sum(x[e,t,v] for t,v in model.shifts_at_day[i+1])) != 0):
             #   partial_weekend_shifts.extend([(e,t,v) for t,v in model.shifts_at_day[i] if x[e,t,v] == 1])
              #  partial_weekend_shifts.extend([(e,t,v) for t,v in model.shifts_at_day[i+1] if x[e,t,v] == 1])

            partial_weekend[e,i] =  abs((sum(x[e,t,v] 
                                    for t,v in model.shifts_at_day[i]) 
                                    - sum(x[e,t,v] 
                                    for t,v in model.shifts_at_day[i+1])))
            # if(partial_weekend[e,i] != abs(model.ro["sat"][e,i].x - model.ro["sun"][e,(i+1)].x)):
            #     print(str(partial_weekend) + "," + str(abs(model.ro["sat"][e,i].x - model.ro["sun"][e,(i+1)].x)))
            #     print(i)
            #     print("Different partial weekends")
    return partial_weekend

def calculate_isolated_working_days(model, x):
    isolated_working_days = {}
    for e in model.employees:
        for i in range(len(model.days)-2):
            isolated_working_days[e,i+1] = max(0,(-sum(x[e,t,v] for t,v in model.shifts_at_day[i]) 
            + sum(x[e,t,v] for t,v in model.shifts_at_day[i+1]) 
            - sum(x[e,t,v] for t,v in model.shifts_at_day[i+2])))

            # if(isolated_working_days[e,i] != model.q_iso["work"][e,i].x):
            #     print("Different isolated working days")

    return isolated_working_days


def calculate_isolated_off_days(model, x):
    isolated_off_days = {}
    for e in model.employees:
        for i in range(len(model.days)-2):
            isolated_off_days[e,i+1] = max(0,(sum(x[e,t,v] for t,v in model.shifts_at_day[i]) 
            - sum(x[e,t,v] for t,v in model.shifts_at_day[i+1]) 
            + sum(x[e,t,v] for t,v in model.shifts_at_day[i+2])-1))
        # if(isolated_off_days[e,i] != model.q_iso["off"][e,i].x):
        #     print("Different isolated off days")
    return isolated_off_days


def calculate_consecutive_days(model, x):
    consecutive_days = {}
    for e in model.employees:
        for i in range(len(model.days)-model.L_C_D):
            consecutive_days[e,i] = max(0,(sum(
                sum(x[e,t,v] for t,v in model.shifts_at_day[i_marked]) 
            for i_marked in range(i,i+model.L_C_D)))- model.L_C_D)
            
            # if(consecutive_days[e,i] != model.q_con[e,i].x):
            #     print("Different consecutive days")
    return consecutive_days

def calculate_f(model, soft_vars, w, employees=None):
    if(employees == None):
        employees = model.employees
    f = {}
    for e in employees:
        f[e] = (sum(w[e,j][1] for j in model.weeks)
            - sum(soft_vars["contracted_hours"][e,j] for j in model.weeks)
            - sum(soft_vars["partial_weekends"][e,i] for i in model.saturdays)
            - sum(soft_vars["isolated_working_days"][e,i+1] + soft_vars["isolated_off_days"][e,i+1] for i in range(len(model.days)-2))
            - sum(soft_vars["consecutive_days"][e,i] for i in range(len(model.days)-model.L_C_D)))
    return f


def calculate_objective_function(model, soft_vars, w):
    f = calculate_f(model, soft_vars, w)
    g = min(f.values())
    objective_function_value = (sum(f.values()) + g - abs(sum(soft_vars["deviation_from_ideal_demand"].values())))
    return objective_function_value, f










#Not needed at the moment and are not in use. Might be deleted at a later time when I know for sure.
def cover_minimum_demand(model, y):
    below_minimum_demand = {}
    for c in model.competencies:
        for t in model.time_periods:
            below_minimum_demand[c,t] = max(0, (model.demand["min"][c,t] - sum(y[c,e,t] for e in model.employee_with_competencies[c])))
    return below_minimum_demand

def under_maximum_demand(model, y):
    above_maximum_demand = {}
    for c in model.competencies:
        for t in model.time_periods:
            above_maximum_demand[c,t] = max(0, (sum(y[c,e,t] for e in model.employee_with_competencies[c]) - model.demand["max"][c,t]))
    return above_maximum_demand

def maximum_one_shift_per_day(model, x):
    more_than_one_shift_per_day = {}
    for e in model.employees:
        for i in model.days:
            more_than_one_shift_per_day[e,i] = max(0, (sum(x[e,t,v] for t,v in model.shifts_at_day[i]) - 1))
    return more_than_one_shift_per_day

def cover_only_one_demand_per_time_period(model, y):
    cover_multiple_demand_periods = {}
    for e in model.employees:
        for t in model.time_periods:
            cover_multiple_demand_periods[e,t] = max(0,(sum(y[c,e,t] for c in model.competencies) - 1))
    return cover_multiple_demand_periods


def one_weekly_off_shift(model, w):
    weekly_off_shift_error = {}
    for e in model.employees:
        for j in model.weeks:
            weekly_off_shift_error[e,j] = max(0,(abs(sum(w[e,t,v] for t,v in model.off_shift_in_week[j]) - 1)))
    return weekly_off_shift_error

#Version 2
def no_work_during_off_shift2(model, w, y):
    no_work_during_off_shift = {}
    for e,t1,v1 in model.w: 
        if w[e,t1,v1] == 1:
            no_work_during_off_shift[e,t1] = sum(y[c,e,t] for c in model.competencies for t in model.t_in_off_shifts[t1,v1])
    return no_work_during_off_shift

#Version 1
def no_work_during_off_shift1(model, w, x):
    no_work_during_off_shift = {}
    for e in model.employees:
        for t,v in model.off_shifts:
           no_work_during_off_shift[e,t,v] = max(0,(len(model.shifts_covered_by_off_shift[t,v]) * w[e,t,v]) - sum((1 - x[e,t_marked, v_marked]) for t_marked, v_marked in model.shifts_covered_by_off_shift[t,v]))
    return no_work_during_off_shift

def mapping_shift_to_demand(model, x, y):
    mapping_shift_to_demand = {}
    for e in model.employees:
        for t in model.time_periods:
           mapping_shift_to_demand[e,t] = max(0,abs(sum(x[e, t_marked, v] for t_marked, v in model.shifts_overlapping_t[t]) - sum(y[c,e,t] for c in model.competencies)))
    return mapping_shift_to_demand


def calculate_positive_deviation_from_contracted_hours(model, y):
    delta_positive_contracted_hours = {}
    for e in model.employees:
        delta_positive_contracted_hours[e] = (
            max(0,
                sum(model.time_step * y[c,e,t] 
                for t in model.time_periods
                for c in model.competencies)
                -  len(model.weeks) * model.contracted_hours[e]))
    return delta_positive_contracted_hours
