from gurobipy import *
from xml_loader.shift_generation import *
import sys
def create_model():
    #MODEL
    model = Model("Employee_scheduling_haakon")

    #SETS
    data = load_data("rproblem2")
    (
        employees, 
        employee_with_competencies, 
        employee_weekly_rest, 
        employee_daily_rest, 
        contracted_hours) = data["employees"]

    (
        time_step, 
        time_periods, 
        time_periods_in_week, 
        days) = data["time"]


    demand = data["demand"]

    (
        shifts_covered_by_off_shift,
        shifts_overlapping_t,
        shifts, 
        shifts_at_day) = data["shifts"]

    (
        t_in_off_shifts,
        off_shifts, 
        off_shift_in_week) = data["off_shifts"]

    competencies = [0]
    weeks = [w for w in range(int(len(days)/7))]
    saturdays = [5 + (i*7) for i in range(len(weeks))]
    L_C_D = 5


    #Variables
    y = model.addVars(competencies, employees, time_periods, vtype=GRB.BINARY, name='y')
    x = model.addVars(employees, shifts, vtype=GRB.BINARY, name='x')
    mu = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='mu')
    w = model.addVars(employees, off_shifts, vtype=GRB.BINARY, name='w')
    lam = model.addVars(employees,vtype=GRB.CONTINUOUS, name='lambda')

    print("#############VARIABLES ADDED#############")


    #Constraints
    model.addConstrs((quicksum(y[c,e,t] 
    for e in employee_with_competencies[c]) == demand["min"][c,t] + mu[c,t]  
    for c in competencies 
    for t in time_periods),
    name='minimum_demand_coverage')

    model.addConstrs((mu[c,t] <= demand["max"][c,t] - demand["min"][c,t]
        for c in competencies 
        for t in time_periods),
    name='mu_less_than_difference')

    model.addConstrs((
        quicksum(x[e,t,v] 
        for t,v in shifts_at_day[i]) 
        <= 1 
        for e in employees 
        for i in days), 
        name="cover_maximum_one_shift")

    model.addConstrs((
        quicksum(x[e,t_marked,v] 
        for t_marked,v in shifts_overlapping_t[t]) 
        == quicksum(y[c,e,t] for c in competencies)
        for e in employees
        for t in time_periods
    ),name="mapping_shift_to_demand")

    model.addConstrs((
        quicksum(y[c,e,t] 
        for c in competencies) 
        <= 1 
        for e in employees 
        for t in time_periods
    ), name="only_cover_one_demand_at_a_time")

    model.addConstrs((
        quicksum(w[e,t,v] 
        for t,v in off_shift_in_week[j]) 
        == 1 
        for e in employees 
        for j in weeks
    ), name="one_weekly_off_shift_per_week")

    model.addConstrs((
        len(shifts_covered_by_off_shift[t,v]) * w[e,t,v] <= 
        quicksum(
            quicksum(
                (1-x[e,t_marked,v_marked]) for c in competencies
            ) for t_marked,v_marked in shifts_covered_by_off_shift[t,v]
        ) for e in employees for t,v in off_shifts
    ), name="no_work_during_off_shift")

    model.addConstrs((
        quicksum(
            quicksum(
                time_step*y[c,e,t] for t in time_periods
            ) for c in competencies
        ) + lam[e] == len(weeks)*contracted_hours[e] for e in employees
    ), name="contracted_hours")


    #Objective Function:
    model.setObjective(
        quicksum(
            quicksum(
                quicksum(
                    y[c,e,t] for e in employees)  
                for c in competencies
            ) for t in time_periods
        ), GRB.MINIMIZE
    )

    print("#############RESTRICTIONS ADDED#############")

    model.setParam("LogFile", "hard_constraint_solution/hard_constraint_log")
    model.optimize()
    model.write("hard_constraint_solution/hard_constraint_log.sol")
    return model

create_model()