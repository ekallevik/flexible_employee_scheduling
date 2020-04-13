
#Different Delta strategies:
#Strategi 1:
def delta_calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_repair_set):
    for c in competencies:
        for e2,t,v in destroy_repair_set:
            for t in t_covered_by_shift[t,v]:
                state.soft_vars["negative_deviation_from_demand"][c,t] = abs(sum(state.y[c,e,t] for e in employee_with_competencies[c]) - demand["ideal"][c,t])


def delta_calculate_negative_deviation_from_contracted_hours(state, repair_set, destroy_set):
    for e,t,v in destroy_set:
        state.soft_vars["contracted_hours"][e] -= v
    
    for e,t,v in repair_set:
        state.soft_vars["contracted_hours"][e] += v


#Weaknesses: 
# 1. It could possibly check the same employee twice
# 2. It checks every weekend instead of only the weekends that have been destroyed or repaired
def calculate_partial_weekends(state, repair_destroy_set, shifts_at_day, saturdays):
    for e,t1,v1 in repair_destroy_set:
        for i in saturdays:
            state.soft_vars["partial_weekends"][e,i] = abs(sum(state.x[e,t,v] for t,v in shifts_at_day[i]) - sum(state.x[e,t,v] for t,v in shifts_at_day[i+1]))

#Weaknesses: 
# 1. It could possibly check the same employee twice
# 2. It checks every possible combination of isolated working days instead of the ones that could be affected by the destroy and repair
def calculate_isolated_working_days(state, repair_destroy_set, shifts_at_day, days):
    for e,t1,v1 in repair_destroy_set:
        for i in range(len(days)-2):
            state.soft_vars["isolated_working_days"][e,i+1] = max(0,(-sum(state.x[e,t,v] for t,v in shifts_at_day[i]) 
            + sum(state.x[e,t,v] for t,v in shifts_at_day[i+1]) 
            - sum(state.x[e,t,v] for t,v in shifts_at_day[i+2])))


#Weaknesses: 
# 1. It could possibly check the same employee twice
# 2. It checks every possible combination of isolated off days instead of the ones that could be affected by the destroy and repair
def calculate_isolated_off_days(state, repair_destroy_set, shifts_at_day, days):
    for e,t1,v1 in repair_destroy_set:
        for i in range(len(days)-2):
            state.soft_vars["isolated_off_days"][e,i+1] = max(0,(sum(state.x[e,t,v] for t,v in shifts_at_day[i]) 
            - sum(state.x[e,t,v] for t,v in shifts_at_day[i+1]) 
            + sum(state.x[e,t,v] for t,v in shifts_at_day[i+2])-1))


#Weaknesses: 
# 1. It could possibly check the same employee twice
# 2. It checks every possible combination of consecutive days instead of the ones that could be affected by the destroy and repair
def calculate_consecutive_days(state, repair_destroy_set, shifts_at_day, L_C_D, days):
    for e,t1,v1 in repair_destroy_set:
        for i in range(len(days)-L_C_D):
            state.soft_vars["consecutive_days"][e,i] = max(0,(sum(sum(state.x[e,t,v] for t,v in shifts_at_day[i_marked]) for i_marked in range(i, i+L_C_D)))- L_C_D)


def calculate_f(state, repair_destroy_set, off_shifts, saturdays, days, L_C_D):
    for e,t1,v1 in repair_destroy_set:
        state.f[e] = (sum(v * state.w[e,t,v] for t,v in off_shifts)
            - state.soft_vars["contracted_hours"][e]
            - sum(state.soft_vars["partial_weekends"][e,i] for i in saturdays)
            - sum(state.soft_vars["isolated_working_days"][e,i+1] for i in range(len(days)-2))
            - sum(state.soft_vars["isolated_off_days"][e,i+1] for i in range(len(days)-2))
            - sum(state.soft_vars["consecutive_days"][e,i] for i in range(len(days)-L_C_D)))


def cover_minimum_demand(state, repair_destroy_set, employee_with_competencies, demand, time_periods, competencies, t_covered_by_shift):
    for c in competencies:
        for e2,t1,v1 in repair_destroy_set:
            for t in t_covered_by_shift[t1,v1]:
                state.hard_vars["below_minimum_demand"][c,t] = max(0, (demand["min"][c,t] - sum(state.y[c,e,t] for e in employee_with_competencies[c])))


def under_maximum_demand(state, repair_destroy_set, employee_with_competencies, demand, time_periods, competencies, t_covered_by_shift):
    for c in competencies:
        for e2,t1,v1 in repair_destroy_set:
            for t in t_covered_by_shift[t1,v1]:
                state.hard_vars["above_maximum_demand"][c,t] = max(0, (sum(state.y[c,e,t] for e in employee_with_competencies[c]) - demand["max"][c,t]))
    
def maximum_one_shift_per_day(state, repair_destroy_set, demand, shifts_at_day, days):
    for e,t,v in repair_destroy_set:
        for i in days:
            state.hard_vars["more_than_one_shift_per_day"][e,i] = max(0, (sum(state.x[e,t,v] for t,v in shifts_at_day[i]) - 1))

def cover_only_one_demand_per_time_period(state, repair_set, t_covered_by_shift, competencies):
    for e,t1,v1 in repair_set:
        for t in t_covered_by_shift[t1,v1]:
            state.hard_vars["cover_multiple_demand_periods"][e,t] = max(0,(sum(state.y[c,e,t] for c in competencies) - 1))

def one_weekly_off_shift(state, repair_destroy_set, weeks, off_shift_in_week):
    for e,t,v in repair_destroy_set:
        for j in weeks:
            state.hard_vars["weekly_off_shift_error"][e,j] = max(0,(abs(sum(state.w[e,t,v] for t,v in off_shift_in_week[j]) - 1)))

def no_work_during_off_shift(state, repair_destroy_set, competencies, t_covered_by_off_shift, off_shifts):
    for e,t2,v2 in repair_destroy_set:
        for t1,v1 in off_shifts: 
            if state.w[e,t1,v1] != 0:
                state.hard_vars["no_work_during_off_shift"][e,t1] = sum(state.y[c,e,t] for c in competencies for t in t_covered_by_off_shift[t1,v1])


def mapping_shift_to_demand(state, repair_destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies):
    for e,t1,v1 in repair_destroy_set:
        for t in t_covered_by_shift[t1,v1]:
           state.hard_vars["mapping_shift_to_demand"][e,t] = max(0, abs(sum(state.x[e, t_marked, v] for t_marked, v in shifts_overlapping_t[t]) - sum(state.y[c,e,t] for c in competencies)))


def calculate_positive_deviation_from_contracted_hours(state, destroy_set, repair_set):
    for e,t,v in destroy_set:
        state.hard_vars["delta_positive_contracted_hours"][e] -= v
    
    for e,t,v in repair_set:
        state.hard_vars["delta_positive_contracted_hours"][e] += v



def calculate_objective_function(state, repair_destroy_set, off_shifts, saturdays, L_C_D, days, competencies):
    calculate_f(state, repair_destroy_set, off_shifts, saturdays, days, L_C_D)
    g = min(state.f.values())
    #Regular objective function
    state.objective_function_value = (sum(state.f.values()) + g - sum(state.soft_vars["negative_deviation_from_demand"].values()))

