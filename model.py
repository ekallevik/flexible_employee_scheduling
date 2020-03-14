from gurobipy import *
from xml_loader.shift_generation import *
import sys

#MODEL
model = Model("Employee_scheduling_haakon")

#SETS
data = load_data("rproblem3")
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
delta_plus = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='delta_plus')
delta_minus = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='delta_minus')
gamma = model.addVars(employees, days, vtype=GRB.BINARY, name='gamma')
w = model.addVars(employees, off_shifts, vtype=GRB.BINARY, name='w')
lam = model.addVars(employees,vtype=GRB.CONTINUOUS, name='lambda')
ro_sat = model.addVars(employees, days, vtype=GRB.BINARY, name='ro_sat')
ro_sun = model.addVars(employees, days, vtype=GRB.BINARY, name='ro_sun')
q_iso_off = model.addVars(employees, days, vtype=GRB.BINARY, name='q_iso_off')
q_iso_work = model.addVars(employees, days, vtype=GRB.BINARY, name='q_iso_work')
q_con = model.addVars(employees, days, vtype=GRB.BINARY, name='q_con')
f_plus = model.addVars(employees, vtype=GRB.CONTINUOUS, name='f_plus')
f_minus = model.addVars(employees, vtype=GRB.CONTINUOUS, name='f_minus')
g_plus = model.addVar(vtype=GRB.CONTINUOUS, name='g_plus')
g_minus = model.addVar(vtype=GRB.CONTINUOUS, name='g_minus')
# k = model.addvars(employees, time_periods, vtype.GRB.BINARY, name='backward_rotation')
print("#############VARIABLES ADDED#############")

weights =   {
                "rest": 5,
                "contracted hours": 1,
                "partial weekends": 1,
                "isolated working days": 1,
                "isolated off days": 1,
                "consecutive days": 1,
                "backward rotation": 1,
                "preferences": 1,
                "lowest fairness score" : 1,
                "demand_deviation" : 5
            }



#Constraints
model.addConstrs((quicksum(y[c,e,t] for e in employee_with_competencies[c]) == demand["min"][c,t] + mu[c,t]  
for c in competencies for t in time_periods),
name='minimum_demand_coverage')

model.addConstrs((mu[c,t] <= demand["max"][c,t] - demand["min"][c,t]
    for c in competencies 
    for t in time_periods),
name='mu_less_than_difference')

model.addConstrs((
    mu[c,t] + demand["min"][c,t] - demand["ideal"][c,t] 
    == delta_plus[c,t] - delta_minus[c,t] 
    for t in time_periods 
    for c in competencies),
name="deviation_from_ideel_demand")

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
    quicksum(x[e,t,v] 
    for t,v in shifts_at_day[i]) 
    == gamma[e,i] 
    for e in employees 
    for i in days
), name="if_employee_e_works_day_i")


model.addConstrs((
    quicksum(w[e,t,v] 
    for t,v in off_shift_in_week[j]) 
    == 1 
    for e in employees 
    for j in weeks
), name="one_weekly_off_shift_per_week")

# Alternativ 2 til off_shift restriksjon (restriksjon 1.10). Virker raskere
model.addConstrs((
    len(shifts_covered_by_off_shift[t,v]) * w[e,t,v] <= 
    quicksum(
        1-x[e,t_marked,v_marked]
        for t_marked,v_marked in shifts_covered_by_off_shift[t,v]
    ) for e in employees for t,v in off_shifts
), name="no_work_during_off_shift")

model.addConstrs((
    quicksum(
        quicksum(
            time_step*y[c,e,t] for t in time_periods
        ) for c in competencies
    ) + lam[e] == len(weeks)*contracted_hours[e] for e in employees
), name="contracted_hours")

#Soft Constraints

model.addConstrs((
    quicksum(
        quicksum(
            time_step*y[c,e,t] for t in time_periods_in_week[j]
        ) for c in competencies
    ) >= 0.1*contracted_hours[e] for e in employees for j in weeks
), name="min_weekly_work_hours")

model.addConstrs((
    quicksum(
        quicksum(
            time_step*y[c,e,t] for t in time_periods_in_week[j]
        ) for c in competencies
    ) <= 1.4*contracted_hours[e] for e in employees for j in weeks
), name="maximum_weekly_work_hours")

model.addConstrs((
    gamma[e,i] - gamma[e,(i+1)] == ro_sat[e,i] - ro_sun[e,(i+1)] for e in employees for i in saturdays
), name="partial_weekends")

model.addConstrs((
    -gamma[e,i] + gamma[e,(i+1)] - gamma[e,(i+2)] <= q_iso_work[e,(i+1)] for e in employees for i in range(len(days)-2)
), name="isolated_working_days")

model.addConstrs((
    gamma[e,i] - gamma[e,(i+1)] + gamma[e,(i+2)] - 1 <= q_iso_off[e,(i+1)] for e in employees for i in range(len(days)-2)
), name="isolated_off_days")

model.addConstrs((
    quicksum(
        gamma[e,i_marked] for i_marked in range(i, i+L_C_D)
    ) - L_C_D <= q_con[e,i] for e in employees for i in range(len(days) - L_C_D)
), name="consecutive_days")

# model.addConstrs((
#     quicksum(x[e,t,v] for t,v in s_br[t])
#     <= k[e,t] + 1
#     for e in employees
#     for t in time_periods
# ), name="backward_rotation")

 
model.addConstrs((
        f_plus[e] - f_minus[e] ==
        weights["rest"] * quicksum(v * w[e,t,v] for t,v in off_shifts)
        - weights["contracted hours"] * lam[e]
        - weights["partial weekends"] * quicksum(ro_sat[e,j] + ro_sun[e,j] for j in weeks)
        - weights["isolated working days"] * quicksum(q_iso_work[e,i] for i in days)
        - weights["isolated off days"] * quicksum(q_iso_off[e,i] for i in days)
        - weights["consecutive days"] * quicksum(q_con[e,i] for i in days)
        for e in employees
        ), name="objective_function_restriction")
            #- weights["backward rotation"] * k[e,i]
            #+weights["preferences"] * quicksum(pref[e,t] for t in time_periods) * quicksum(y[c,e,t] for c in competencies)
        



model.addConstrs((
    g_plus - g_minus <= f_plus[e] - f_minus[e] for e in employees)
    , name="lowest_fairness_score")

#Objective Function:
model.setObjective(
            quicksum(f_plus[e] - f_minus[e] for e in employees)
            + weights["lowest fairness score"] * (g_plus - g_minus)
            - weights["demand_deviation"] *
            quicksum(
                quicksum(
                    delta_plus[c, t] + delta_minus[c, t] for t in time_periods
            ) for c in competencies
            )
            ,GRB.MAXIMIZE)

print("#############RESTRICTIONS ADDED#############")


model.optimize()

