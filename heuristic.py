from model_class import *
from xml_loader.shift_generation import load_data


model = Optimization_model("rproblem2")
model.add_variables()
model.add_constraints()
model.set_objective()
model.optimize()

x = model.x
y = model.y
w = model.w

# for e in model.employees:
#     for t,v in model.off_shifts:
#         if(w[e,t,v].x == 1):
#             print(e,t,v)
def calculate_deviation_from_demand():

    delta = {}
    for c in model.competencies:
        for t in model.time_periods:
            delta[c,t] = abs(sum(model.y[c,e,t].x for e in model.employee_with_competencies[c]) - model.demand["ideal"][c,t])
            if(delta[c,t] - abs(model.delta["plus"][c,t].x - model.delta["minus"][c,t].x)) != 0:
                print(delta[c,t] - abs(model.delta["plus"][c,t].x - model.delta["minus"][c,t].x))
                print("Different Delta")
    return delta

    model.addConstrs((
        quicksum(
            quicksum(
                time_step*y[c,e,t] for t in time_periods
            ) for c in competencies
        ) + lam[e] == len(weeks)*contracted_hours[e] for e in employees
    ), name="contracted_hours")

def calculate_deviation_from_contracted_hours():
    delta_contracted_hours = {}
    for e in model.employees:
        delta_contracted_hours[e] = (len(model.weeks) * model.contracted_hours[e] - sum(
            sum(
                model.time_step * y[c,e,t].x for t in model.time_periods
            ) for c in model.competencies
        ))
    return delta_contracted_hours

def calculate_partial_weekends():
    partial_weekend = {}
    print("Partial Weekends")
    for e in model.employees:
        for i in model.saturdays:
            partial_weekend[e,i] = abs((sum(model.x[e,t,v].x for t,v in model.shifts_at_day[i]) - sum(model.x[e,t,v].x for t,v in model.shifts_at_day[i+1])))
            if(partial_weekend[e,i] != abs(model.ro["sat"][e,i].x - model.ro["sun"][e,(i+1)].x)):
                print(str(partial_weekend) + "," + str(abs(model.ro["sat"][e,i].x - model.ro["sun"][e,(i+1)].x)))
                print(i)
                print("Different partial weekends")
    return partial_weekend

def calculate_isolated_working_days():
    isolated_working_days = {}
    for e in model.employees:
        for i in range(len(model.days)-2):
            isolated_working_days[e,i] = max(0,(-sum(x[e,t,v].x for t,v in model.shifts_at_day[i]) 
            + sum(x[e,t,v].x for t,v in model.shifts_at_day[i+1]) 
            - sum(x[e,t,v].x for t,v in model.shifts_at_day[i+2])))

            if(isolated_working_days[e,i] != model.q_iso["work"][e,i].x):
                print("Different isolated working days")

    return isolated_working_days


def calculate_isolated_off_days():
    isolated_off_days = {}
    for e in model.employees:
        for i in range(len(model.days)-2):
            isolated_off_days[e,i+1] = max(0,(sum(x[e,t,v].x for t,v in model.shifts_at_day[i]) 
            - sum(x[e,t,v].x for t,v in model.shifts_at_day[i+1]) 
            + sum(x[e,t,v].x for t,v in model.shifts_at_day[i+2])-1))
        if(isolated_off_days[e,i] != model.q_iso["off"][e,i].x):
            print("Different isolated off days")
    return isolated_off_days

def calculate_consecutive_days():
    consecutive_days = {}
    for e in model.employees:
        for i in range(len(model.days)-model.L_C_D):
            consecutive_days[e,i] = max(0,(sum(
                sum(x[e,t,v].x for t,v in model.shifts_at_day[i_marked]) 
            for i_marked in range(i,i+model.L_C_D)))- model.L_C_D)
            
            if(consecutive_days[e,i] != model.q_con[e,i].x):
                print("Different consecutive days")
    return consecutive_days

def calculate_objective_function():
    partial_weekend = calculate_partial_weekends()
    q_iso_work = calculate_isolated_working_days()
    q_iso_off = calculate_isolated_off_days()
    q_con = calculate_consecutive_days()
    delta = calculate_deviation_from_demand()
    delta_c = calculate_deviation_from_contracted_hours()
    f = {}
    for e in model.employees:
        f[e] = (sum(v * w[e,t,v].x for t,v in model.off_shifts)
            - delta_c[e]
            - sum(partial_weekend[e,i] for i in model.saturdays)
            - sum(q_iso_work[e,i] for i in range(len(model.days)-2))
            - sum(q_iso_off[e,i+1] for i in range(len(model.days)-2))
            - sum(q_con[e,i] for i in range(len(model.days)-model.L_C_D)))
        print(str(f[e]) + ", " + str(model.f["plus"][e].x-model.f["minus"][e].x))
    g = min(f.values())

    objective =    (sum(f[e] for e in model.employees)
                    + g
                    - sum(sum(delta[c,t] for t in model.time_periods) for c in model.competencies)
                    )

    print(objective)


def cover_minimum_demand():
    for c in model.competencies:
        for t in model.time_periods:
            sum(y[c,e,t].x for e in model.employee_with_competencies[c]) - model.demand["min"][c,t]

def under_maximum_demand():
    for c in model.competencies:
        for t in model.time_periods:
            model.demand["max"] - sum(y[c,e,t].x for e in model.employee_with_competencies[c])

def maximum_one_shift_per_day():
    for e in model.employees:
        for i in model.days:
            1 - sum(x[e,t,v].x for t,v in model.shifts_at_day[i])

def cover_only_one_demand_per_time_period():
    for e in model.employees:
        for t in model.time_periods:
            1 - sum(y[c,e,t].x for c in model.competencies)

def one_weekly_off_shift():
    for e in model.employees:
        for j in model.weeks:
            abs(1 - sum(w[e,t,v].x for t,v in model.off_shift_in_week[j]))


def no_work_during_off_shift():
    for e in model.employees:
        for t,v in model.off_shifts:
            (len(model.shifts_covered_by_off_shift[t,v]) * model.w[e,t,v])

            sum((1 - x[e,t_marked, v_marked]) for t_marked, v_marked in model.shifts_covered_by_off_shift[t,v])
            
calculate_objective_function()