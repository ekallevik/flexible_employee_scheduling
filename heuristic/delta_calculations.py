
#Different Delta strategies:
#Strategy 1:
def delta_calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_repair_set):
    for c in competencies:
        for e2,t,v in destroy_repair_set:
            for t in t_covered_by_shift[t,v]:
                state.soft_vars["negative_deviation_from_demand"][c,t] = abs(sum(state.y[c,e,t] for e in employee_with_competencies[c]) - demand["ideal"][c,t])


def delta_calculate_negative_deviation_from_contracted_hours(state, employees, contracted_hours, weeks, time_periods, competencies, time_step):
    """
    Calculates both negative and positive contracted hours (The name should be updated but haven't had time yet)
    It checks the employees where a change has been made whether destroyed or repaired. 
    Then calculates the deviation only for these employees
    
    I have decided to also include checking the hard constraint if we are above contracted hours in this function as well
    This is done as it is easy to do at the same time and saveds time.
    Another update comes in another PR that updates the soft variables of contracted hours to weekly contracted hours
    """
    for e in employees:
            deviation_contracted_hours = (contracted_hours[e] - sum(time_step * state.y[c,e,t] for t in time_periods
                for c in competencies))
            if(deviation_contracted_hours >= 0):
                state.soft_vars["contracted_hours"][e] = deviation_contracted_hours
            else:  
                state.hard_vars["delta_positive_contracted_hours"][e] = -deviation_contracted_hours

#I have let this be here on purpose as this was the original though on how this should be done
#The reason it is commented out is beacuse calculating this in destroy/repair ruins this way of calculating contracted hours 
#Left to be used another time perhaps or deleted
    # for e,t,v in destroy_set:
    #     state.soft_vars["contracted_hours"][e] += v

    # for e,t,v in repair_set:
    #     state.soft_vars["contracted_hours"][e] -= v


#Weaknesses: 
# 1. It checks every weekend instead of only the weekends that have been destroyed or repaired
def calculate_partial_weekends(state, employees, shifts_at_day, saturdays):
    for e in employees:
        for i in saturdays:
            state.soft_vars["partial_weekends"][e,i] = abs(sum(state.x[e,t,v] for t,v in shifts_at_day[i]) - sum(state.x[e,t,v] for t,v in shifts_at_day[i+1]))

#Weaknesses: 
# 1. It checks every possible combination of isolated working days instead of the ones that could be affected by the destroy and repair
def calculate_isolated_working_days(state, employees, shifts_at_day, days):
    for e in employees:
        for i in range(len(days)-2):
            state.soft_vars["isolated_working_days"][e,i+1] = max(0,(-sum(state.x[e,t,v] for t,v in shifts_at_day[i]) 
            + sum(state.x[e,t,v] for t,v in shifts_at_day[i+1]) 
            - sum(state.x[e,t,v] for t,v in shifts_at_day[i+2])))


#Weaknesses: 
# 1. It checks every possible combination of isolated off days instead of the ones that could be affected by the destroy and repair
def calculate_isolated_off_days(state, employees, shifts_at_day, days):
    for e in employees:
        for i in range(len(days)-2):
            state.soft_vars["isolated_off_days"][e,i+1] = max(0,(sum(state.x[e,t,v] for t,v in shifts_at_day[i]) 
            - sum(state.x[e,t,v] for t,v in shifts_at_day[i+1]) 
            + sum(state.x[e,t,v] for t,v in shifts_at_day[i+2])-1))


#Weaknesses: 
# 1. It checks every possible combination of consecutive days instead of the ones that could be affected by the destroy and repair
def calculate_consecutive_days(state, employees, shifts_at_day, L_C_D, days):
    for e in employees:
        for i in range(len(days)-L_C_D):
            state.soft_vars["consecutive_days"][e,i] = max(0,(sum(sum(state.x[e,t,v] for t,v in shifts_at_day[i_marked]) for i_marked in range(i, i+L_C_D)))- L_C_D)


def calculate_f(state, employees, off_shifts, saturdays, days, L_C_D):
    """
        Calculates f of employees that have had a change either destroy or repair. 
        It only sums up the different parts and sets the already created f variables of that employee to the new value.
    """
    for e in employees:
        state.f[e] = (sum(v * state.w[e,t,v] for t,v in off_shifts)
            - state.soft_vars["deviation_contracted_hours"][e]
            - sum(state.soft_vars["partial_weekends"][e,i] for i in saturdays)
            - sum(state.soft_vars["isolated_working_days"][e,i+1] for i in range(len(days)-2))
            - sum(state.soft_vars["isolated_off_days"][e,i+1] for i in range(len(days)-2))
            - sum(state.soft_vars["consecutive_days"][e,i] for i in range(len(days)-L_C_D)))

# From here on down we calculate the hard variables (how many times we break a hard contraint)
def below_minimum_demand(state, repair_destroy_set, employee_with_competencies, demand, time_periods, competencies, t_covered_by_shift):
    for c in competencies:
        for e2,t1,v1 in repair_destroy_set:
            for t in t_covered_by_shift[t1,v1]:
                state.hard_vars["below_minimum_demand"][c,t] = max(0, (demand["min"][c,t] - sum(state.y[c,e,t] for e in employee_with_competencies[c])))


def above_maximum_demand(state, repair_destroy_set, employee_with_competencies, demand, time_periods, competencies, t_covered_by_shift):
    for c in competencies:
        for e2,t1,v1 in repair_destroy_set:
            for t in t_covered_by_shift[t1,v1]:
                state.hard_vars["above_maximum_demand"][c,t] = max(0, (sum(state.y[c,e,t] for e in employee_with_competencies[c]) - demand["max"][c,t]))
    
def more_than_one_shift_per_day(state, employees, demand, shifts_at_day, days):
    for e in employees:
        for i in days:
            state.hard_vars["more_than_one_shift_per_day"][e,i] = max(0, (sum(state.x[e,t,v] for t,v in shifts_at_day[i]) - 1))

def cover_multiple_demand_periods(state, repair_set, t_covered_by_shift, competencies):
    for e,t1,v1 in repair_set:
        for t in t_covered_by_shift[t1,v1]:
            state.hard_vars["cover_multiple_demand_periods"][e,t] = max(0,(sum(state.y[c,e,t] for c in competencies) - 1))

def weekly_off_shift_error(state, employees, weeks, off_shift_in_week):
    for e in employees:
        for j in weeks:
            state.hard_vars["weekly_off_shift_error"][e,j] = max(0,(abs(sum(state.w[e,t,v] for t,v in off_shift_in_week[j]) - 1)))

def no_work_during_off_shift(state, employees, competencies, t_covered_by_off_shift, off_shifts):
    for e in employees:
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

# This is needed here to calculate a new objective function with penalty part included. 
def hard_constraint_penalties(state):
    below_demand = sum(state.hard_vars["below_minimum_demand"].values())
    above_demand = sum(state.hard_vars["above_maximum_demand"].values())
    break_one_shift_per_day = sum(state.hard_vars["more_than_one_shift_per_day"].values())
    break_one_demand_per_time = sum(state.hard_vars["cover_multiple_demand_periods"].values())
    break_weekly_off = sum(state.hard_vars["weekly_off_shift_error"].values())
    break_no_work_during_off_shift = sum(state.hard_vars["no_work_during_off_shift"].values())
    break_shift_to_demand = sum(state.hard_vars["mapping_shift_to_demand"].values())
    break_contracted_hours = sum(state.hard_vars["delta_positive_contracted_hours"].values())

    hard_penalties = (  below_demand +  above_demand + break_one_shift_per_day + break_one_demand_per_time + 
                        break_weekly_off + break_no_work_during_off_shift + break_shift_to_demand +
                        break_contracted_hours)
    return hard_penalties

def calculate_objective_function(state, employees, off_shifts, saturdays, L_C_D, days, competencies):
    calculate_f(state, employees, off_shifts, saturdays, days, L_C_D)
    g = min(state.f.values())
    #Regular objective function
    state.objective_function_value = (sum(state.f.values()) + g - sum(state.soft_vars["negative_deviation_from_demand"].values()) - hard_constraint_penalties(state))

