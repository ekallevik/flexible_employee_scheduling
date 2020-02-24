from gurobipy import *
from xml_loader.xml_loader import *
#MODEL
model = Model("Employee_scheduling_haakon")


#SETS
employees, employee_with_competencies, employee_weekly_rest, employee_daily_rest = get_employee_lists()
competencies = [0]
time_periods = get_time_periods()
demand_min, demand_ideal, demand_max = get_demand_periods()
shifts, shifts_at_day = get_shift_lists()
days = get_days()
shifts_overlapping_t = get_shifts_overlapping_t()


#Variables
y = model.addVars(competencies, employees, time_periods, vtype=GRB.BINARY, name='y')
x = model.addVars(employees, shifts, vtype=GRB.BINARY, name='x')
mu = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='mu')
delta_plus = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='delta_plus')
delta_minus = model.addVars(competencies, time_periods, vtype=GRB.INTEGER, name='delta_minus')
gamma = model.addVars(employees, days, vtype=GRB.BINARY, name='gamma')

#Constraints
model.addConstrs((quicksum(y[c, e, t] for e in employee_with_competencies[c]) == demand_min[c,t] + mu[c,t]  
for c in competencies for t in time_periods),
name='minimum_demand_coverage')

model.addConstrs((mu[c,t] <= demand_max[c,t] - demand_min[c,t]
    for c in competencies 
    for t in time_periods),
name='mu_less_than_difference')

model.addConstrs((
    mu[c,t] + demand_min[c,t] - demand_ideal[c,t] 
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
    for e in employees 
    for t,v in shifts_at_day[i]) 
    == gamma[e,i] 
    for e in employees 
    for i in days
), name="if_employee_e_works_day_i")

model.write("out.lp")
"""
def objective_restriction(self):
    model.addConstrs((
        f[e] ==  
            weight_contract * l[e]
            - weight_weekends * 
                quicksum(ro_sat[e,j] + ro_sun[e,j] 
                for j in saturdays)
            + 2*weight_preferences[e] * 
                quicksum(
                        preferences[e,t]*
                        quicksum(
                                y[c,e,t] 
                                for c in competencies)
                        for t in time_periods)
            + weight_rest * 
                quicksum(
                    quicksum(
                        quicksum(
                            (v - employee_rest_weekly[e]) * z[e,t,v]
                            for t in all_time_periods
                        if t >= offset_week_employee[e]+j*hours_in_week 
                        and t < offset_week_employee[e]+(j+1)*hours_in_week-(v))
                        for v in weekly_off_durations)
                    for j in weeks
                    )
            - weight_consecutive_days * 
                quicksum(
                    q_con[e,i] 
                    for i in days)
            - weight_isolated_work * 
                quicksum(
                    q_iso_work[e,i] 
                    for i in days)
            - weight_isolated_off *
                quicksum(
                    q_iso_off[e,i] 
                    for i in days)
            - weight_rot * 
                quicksum(
                    gamma[e,i] 
                    for i in days)
    for e in employees),
    name="objective_function_restriction")


    model.addConstrs((
        g <= f[e] for e in employees)
        ,name="lowest_fairness_score")

def add_variables(self):
    w = model.addVars(employees, days, vtype=GRB.BINARY, name='w')
    ro_sat = model.addVars(employees, days, vtype=GRB.BINARY, name='ro_sat')
    ro_sun = model.addVars(employees, days, vtype=GRB.BINARY, name='ro_sun')
    z = model.addVars(employees, all_time_periods, off_durations, vtype=GRB.BINARY, name='z')
    gamma = model.addVars(employees, days, vtype=GRB.BINARY, name='gamma')
    q_con = model.addVars(employees, days, vtype=GRB.BINARY, name='q_con')
    q_iso_off = model.addVars(employees, days, vtype=GRB.BINARY, name='q_iso_off')
    q_iso_work = model.addVars(employees, days, vtype=GRB.BINARY, name='q_iso_work')
    l = model.addVars(employees,vtype=GRB.INTEGER, name='lambda')
    delta_plus = model.addVars(competencies, shifts_work, time_periods, vtype=GRB.INTEGER, name='delta_plus')
    delta_minus = model.addVars(competencies, shifts_work, time_periods, vtype=GRB.INTEGER, name='delta_minus')
    f = model.addVars(employees, vtype=GRB.CONTINUOUS, name='f')
    g = model.addVar(vtype=GRB.CONTINUOUS, name='g')

    model.update()
    #Set variable parameters

    #Used to fix the possible shift starting times to a number of predefined times. 
    #for key in fixed_shift_times:
        #   x[key].ub = 0

    for var in delta_plus:
        delta_plus[var].lb = 0
        delta_minus[var].lb = 0


    
    for key in x_dict.keys():
        x[key].ub = 0


def add_objective(self):
    model.setObjective(
        quicksum(f[e] for e in employees)
        + weight_lowest_fairness_score * g
        - weight_demand_deviation*
        quicksum(
            quicksum(
                quicksum(
                    delta_plus[c,s,t] + delta_minus[c,s,t] for t in time_periods
                ) for s in shifts_work
            ) for c in competencies
        )
        ,GRB.MAXIMIZE)
"""