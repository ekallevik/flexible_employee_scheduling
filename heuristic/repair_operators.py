from heuristic.delta_calculations import delta_calculate_deviation_from_demand, delta_calculate_negative_deviation_from_contracted_hours, calculate_weekly_rest, calculate_partial_weekends, calculate_isolated_working_days, calculate_isolated_off_days, calculate_consecutive_days, calc_weekly_objective_function, cover_multiple_demand_periods, more_than_one_shift_per_day, above_maximum_demand, below_minimum_demand, calculate_deviation_from_demand, regret_objective_function, mapping_shift_to_demand, calculate_daily_rest_error
from operator import itemgetter
from heuristic.converter import set_x
from random import choice, choices
import numpy as np

def worst_week_repair(shifts_in_week, competencies, t_covered_by_shift, employee_with_competencies, employee_with_competency_combination, demand, time_step, time_periods_in_week, employees, contracted_hours, weeks, shifts_at_day, state, destroy_set, week):
    """
        A greedy repair operator based on destroying the worst week.
        The last three arguments are passed from its corresponding destroy operator.

        It finds the shift with highest deviation from demand.
        This shift is then assigned to the employee with highest deviation from contracted hours
        as long as that employee does not work on the day of the shift we are assigning. 

        It continues to do so until either the total negative deviation from demand is below a threshold (6)
        or we do not have any employees to assign to this shift as all employees are working this day 
    """
    repair_set = []
    employees_changed = employees
    changed = destroy_set.copy()
    impossible_shifts = []


    while(True):
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, changed)
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)

        shifts = {
                (t1, v1, comp):
                sum(
                    state.soft_vars["deviation_from_ideal_demand"].get((c, t), 0)
                    for c in competencies
                    for t in t_covered_by_shift[t1, v1]
                )
                - (20*(len(competencies)-1) + v1)
                for comp in employee_with_competency_combination
                for t1, v1 in shifts_in_week[week[0]]
                if (t1, v1, comp) not in impossible_shifts
                }
         
        shift = max(shifts.items(), key=itemgetter(1))[0]
        competency_pair = shift[2]

        deviation_from_demand = -sum(state.soft_vars["deviation_from_ideal_demand"][c,t] 
                                    for c in shift[2]
                                    for t in t_covered_by_shift[shift[0], shift[1]] 
                                    if (c, t) in state.soft_vars["deviation_from_ideal_demand"] 
                                    if state.soft_vars["deviation_from_ideal_demand"][c,t] < 0)

        if(deviation_from_demand <= 6):
            return repair_set
        
        
        y_s_1 = {
            t: {
                c: state.soft_vars["deviation_from_ideal_demand"][c, t]
                for c in competency_pair
                if (c, t) in state.soft_vars["deviation_from_ideal_demand"]
            }
            for t in t_covered_by_shift[shift[0], shift[1]]
        }

        y_s = [
            min(y_s_1[t].items(), key=itemgetter(1))[0]
            for t in t_covered_by_shift[shift[0], shift[1]]
            if len(y_s_1[t]) != 0
        ]
        competencies_needed = tuple(set(y_s))

        
        deviation_contracted_hours = {e: (sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks)  
                                    - (competency_level - len(competencies_needed)))
                                    + (20 if (sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) - shift[1] >= 8.5) else 0)
                                    + (20 if (sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) - shift[1] <= 17) else 0)
                                    + (100 if (sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) - shift[1]  == 0) else 0)
                                    for (competency_level, e) in employee_with_competency_combination[competencies_needed] 
                                    if (sum(state.x[e,t,v] for t,v in shifts_at_day[int(shift[0]/24)])) == 0}


        if(len(deviation_contracted_hours.keys()) == 0):
            impossible_shifts.append(shift)
            continue

        e = max(deviation_contracted_hours.items(), key=itemgetter(1))[0]

        repair_set.append(set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1, y_s))
        employees_changed = [e]
        changed = [(e, shift[0], shift[1])]





def worst_week_regret_repair(   shifts_in_week, competencies, t_covered_by_shift, employee_with_competencies, employee_with_competency_combination,
                                 demand, time_step, time_periods_in_week, combined_time_periods_in_week, employees, contracted_hours, 
                                 invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, 
                                 weeks, shifts_at_day, L_C_D, shifts_overlapping_t, state, destroy_set, week):
    """
        The decision variables are set in the destroy operator. This only applies to the x and y variables as w now is a implisit variable that should be calculated
        At the beginning of a repair operator the soft variables and hard penalizing variables have not been updated to reflect the current changes to the decision variables

        To be able to calculate the deviation from demand (as this is how we choose a shift to assign) we would have to update the deviation from demand for the shifts (t_covered_by_shift) that have been destroyed.
        This is done efficiently in delta_calcualte_deviation_from_demand. It only checks the destroyed shifts (and their t's) and only in a negative direction (covering to much demand would give 0 in deviation)

        If the total deviation from demand (for the week/s in question) are below a threshold (6) we are satisfied and would return the repair_set with shifts (e,t,v) set

        If not we take the shift with highest deviation from demand (in the weeks in question) to be assigned. 
        We only search for an employee to assign to this shift based on if the employee are not working the day the shift is on.

        Which hard variables are important to calculate?:
            1.  Above/Below demand is done on a destroy_repair_set basis. This means we would have to calculate the above and below to get correct hard variables here if they were broken before the destroy fixes it. 
                A good thing here is that if we do so with the destroy_set we fix the entire week. This means we have a fresh start with no broken constraints this week.
            2.  More than one shift per day is calculated on a employee basis. It checks every day on that employee. This would have to be done before as we need it in the calculation. We cannot do this on each employee as we loop through them.
                We do have the days we would check though. Would also not need to do a calculation on these hard constraints, but rather just set them to 0. Most likely this is faster. 
            3.  Cover multiple demand periods are also done on a destroy_repair_set basis. It would have to be run before. 
            4.  Mapping shift to demand is also done on a destroy_repair_set basis. Would have to be run before to start fresh. 
            5.  Positive contracted hours. This is run together with negative contracted hours. This is done on a employee and week basis. By not running it before for all employees we would not have updated the contracted hours after the destroy when calculating the new objective function. 
                This would result in a wrong objective value. 
            6.  Weekly rest. When a week have been destroyed everyone starts with a full week of rest if calculated. If not we would continue with the rest they had before. The smartest move would be to start fresh here as well. 

        Which soft variables are important to calculate?:
            1. Partial weekend are only depending on the employee. It is calculated for every week no matter what as it is not based on destroy_repair_set
            2. The same is true for isolated working days, isolated off days and consecutive days

    """


    repair_set = []
    #All employees gets changed in this operator atm. Employees changed are therefore set to all employees at the beginning.
    employees_changed = employees
    #Destroy_set is the shifts that have been destroyed.
    destroy_set = destroy_set.copy()
    saturdays = [5 + j * 7 for j in week]
    days = [i + (7 * j) for j in week for i in range(7)]
    impossible_shifts = []
    daily_destroy_and_repair = [destroy_set, []]
    while(True):
        #Initial phase to recalculate soft and hard variables of the destroyed weeks
        #Calculates deviation from demand first to see if we are done and can return
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)

        shifts =    {(t1, v1, competencies_1): -sum(state.soft_vars["deviation_from_ideal_demand"][c,t] for c in competencies_1 for t in t_covered_by_shift[t1, v1] if (c,t) in state.soft_vars["deviation_from_ideal_demand"]) 
                                            - (20*(len(competencies_1)-1) + v1) for competencies_1 in employee_with_competency_combination for t1, v1 in shifts_in_week[week[0]] if (t1,v1,competencies_1) not in impossible_shifts
                    }
        
        shift = max(shifts.items(), key=itemgetter(1))[0]

        deviation_from_demand = -sum(state.soft_vars["deviation_from_ideal_demand"][c,t]
                                    for c in shift[2]
                                    for t in t_covered_by_shift[shift[0], shift[1]]
                                    if (c, t) in state.soft_vars["deviation_from_ideal_demand"] 
                                    if state.soft_vars["deviation_from_ideal_demand"][c,t] < 0)

        y_s_1 = {t: {(c): state.soft_vars["deviation_from_ideal_demand"][c,t] for c in shift[2] if (c,t) in state.soft_vars["deviation_from_ideal_demand"]} for t in t_covered_by_shift[shift[0], shift[1]]}
        y_s = [min(y_s_1[t].items(), key=itemgetter(1))[0] for t in t_covered_by_shift[shift[0], shift[1]] if len(y_s_1[t]) != 0]
        competencies_needed = tuple(set(y_s))
        possible_employees = [(e, score) for score, e in employee_with_competency_combination[competencies_needed] if (sum(state.x[e,t,v] for t,v in shifts_at_day[int(shift[0]/24)])) == 0]

        if(len(possible_employees) == 0):
            impossible_shifts.append(shift)
            continue

        if(deviation_from_demand < 6 or max([sum(state.soft_vars["deviation_contracted_hours"][e[0],j] for j in week) for e in possible_employees]) < shift[1]):
            deviation_from_demand = -sum(state.soft_vars["deviation_from_ideal_demand"][c,t] for c in competencies for t in time_periods_in_week[c, week[0]] if state.soft_vars["deviation_from_ideal_demand"][c,t] < 0)
            return repair_set 


        #Hard Restrictions/Variables
        cover_multiple_demand_periods(state, destroy_set, t_covered_by_shift, competencies)
        more_than_one_shift_per_day(state, employees_changed, demand, shifts_at_day, days)
        above_maximum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        mapping_shift_to_demand(state, destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies)

        #Soft Restrictions/Variables
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        calculate_partial_weekends(state, employees_changed, shifts_at_day, saturdays)
        calculate_isolated_working_days(state, employees_changed, shifts_at_day, days)
        calculate_isolated_off_days(state, employees_changed, shifts_at_day, days)
        calculate_consecutive_days(state, employees_changed, shifts_at_day, L_C_D, days)
        calculate_weekly_rest(state, shifts_in_week, employees_changed, week)
        calculate_daily_rest_error(state, daily_destroy_and_repair, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest)


        #Now we have to decide on which employee should be assigned this shift.
        #Since we want to do this through regret we have to calculate the objective function of the state with that shift assigned to each employee.
        #We have two options here:
        # 1. We could copy the state we are working with. We would have to use deepcopy which takes time and resources.
        # 2. We could set the x value and then remove it again after calculation. Might take a lot of time and resources. 

        #Copy method
        objective_values = {}
        for e, score in possible_employees:
            current_state = state.copy()
            repaired = [set_x(current_state, t_covered_by_shift, e, shift[0], shift[1], 1, y_s)]

            #Soft restriction calculations
            calculate_deviation_from_demand(current_state, competencies, t_covered_by_shift, employee_with_competencies, demand, repaired)
            calculate_weekly_rest(current_state, shifts_in_week, [e], week)
            calculate_partial_weekends(current_state, [e], shifts_at_day, saturdays)
            calculate_isolated_working_days(current_state, [e], shifts_at_day, days)
            calculate_isolated_off_days(current_state, [e], shifts_at_day, days)
            calculate_consecutive_days(current_state, [e], shifts_at_day, L_C_D, days)
            delta_calculate_negative_deviation_from_contracted_hours(current_state, [e], contracted_hours, weeks, time_periods_in_week, competencies, time_step)
            #Hard constraint calculations
            mapping_shift_to_demand(state, repaired, t_covered_by_shift, shifts_overlapping_t, competencies)
            cover_multiple_demand_periods(state, repaired, t_covered_by_shift, competencies)
            more_than_one_shift_per_day(current_state, [e], demand, shifts_at_day, days)
            above_maximum_demand(current_state, repaired, employee_with_competencies, demand, competencies, t_covered_by_shift)
            below_minimum_demand(current_state, repaired, employee_with_competencies, demand, competencies, t_covered_by_shift)
            calculate_daily_rest_error(state, [[], repaired], invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest)

            competency_score = score - len(competencies_needed)
            #Calculate the objective function when the employee e is assigned the shift
            objective_values[e] = calc_weekly_objective_function(current_state, competencies, time_periods_in_week, combined_time_periods_in_week, employees, week, L_C_D, competency_score=competency_score)[0]

        max_value = max(objective_values.items(), key=itemgetter(1))[1]
        employee = choice([key for key, value in objective_values.items() if value == max_value])
        repair_set.append(set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1, y_s))
        employees_changed = [employee]
        destroy_set = [(employee, shift[0], shift[1])]
        daily_destroy_and_repair = [[], destroy_set]





def worst_employee_repair(competencies, t_covered_by_shift, employee_with_competencies, employee_with_competency_combination, demand, contracted_hours, weeks, time_periods_in_week, time_step, all_shifts, shifts_at_day, state, destroy_set, employees):
    """
        A greedy repair operator based on destroying the worst employee.
        The last three arguments are passed from its corresponding destroy operator.

        It finds the shift with highest deviation from demand.
        This shift is then assigned to the employee with highest deviation from contracted hours
        as long as that employee does not work on the day of the shift we are assigning. 
        The difference between this operator and the worst week is that we only look at the employees we have destroyed in the destroy operator

        It continues to do so until either the total negative deviation from demand is below a threshold (6)
        or we do not have any employees to assign to this shift as all employees are working this day 
    """
    
    repair_set = []
    destroy_set = destroy_set.copy()
    employees_changed = employees
    allowed_competency_combinations = {combination for combination in employee_with_competency_combination for item in employee_with_competency_combination[combination] for e in employees_changed if e == item[1]}
    while(True):
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)
        shifts = {
            (t1, v1, competencies): -sum(
                state.soft_vars["deviation_from_ideal_demand"][c, t]
                for competencies in allowed_competency_combinations
                for c in competencies
                for t in t_covered_by_shift[t1, v1]
                if state.soft_vars["deviation_from_ideal_demand"].get((c, t))
            )
            - (20 * (len(competencies) - 1) + v1)
            for competencies in allowed_competency_combinations
            for t1, v1 in all_shifts
        }
        shift = max(shifts.items(), key=itemgetter(1))[0]

        y_s = [
            min(
                {c: state.soft_vars["deviation_from_ideal_demand"][c, t] for c in shift[2]}.items(),
                key=itemgetter(1),
            )[0]
            for t in t_covered_by_shift[shift[0], shift[1]]
        ]
        competencies_needed = tuple(set(y_s))

                
        deviation_from_demand = -sum(state.soft_vars["deviation_from_ideal_demand"][c,t] for competencies_2 in allowed_competency_combinations for c in competencies_2 for t in t_covered_by_shift[shift[0], shift[1]] if (c, t) in state.soft_vars["deviation_from_ideal_demand"] if state.soft_vars["deviation_from_ideal_demand"][c,t] < 0)
        if(deviation_from_demand < 6):
            print("WE: Deviation from demand: " + str(deviation_from_demand))
            return repair_set

        
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        deviation_contracted_hours = {
            e: (
                sum(state.soft_vars["deviation_contracted_hours"][e, j] for j in weeks)
                - 10 * (competency_level - len(competencies_needed))
            )
            for (competency_level, e) in employee_with_competency_combination[competencies_needed]
            if (sum(state.x[e, t, v] for t, v in shifts_at_day[int(shift[0] / 24)])) == 0
            if e in employees_changed
        }

        if(len(deviation_contracted_hours.keys()) == 0):
            return repair_set
        e = max(deviation_contracted_hours.items(), key=itemgetter(1))[0]

        repair_set.append(set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1, y_s))
        employees_changed = [e]
        destroy_set = [(e, shift[0], shift[1])]



def worst_employee_regret_repair(   competencies, t_covered_by_shift, employee_with_competencies, employee_with_competency_combination, demand, 
                                    all_shifts, off_shifts, saturdays, days, L_C_D, weeks, shifts_at_day, shifts_in_week, contracted_hours,
                                    invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, 
                                    time_periods_in_week, time_step, shifts_overlapping_t, state, destroy_set, employees_changed):

    #print("worst_employee_regret_repair is running")
    repair_set = []
    destroy_set = destroy_set.copy()
    allowed_competency_combinations = {combination for combination in employee_with_competency_combination for item in employee_with_competency_combination[combination] for e in employees_changed if e == item[1]}
    daily_destroy_and_repair = [destroy_set, []]
    while(True):
        calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)

        shifts = {
            (t1, v1, competencies): -sum(
                state.soft_vars["deviation_from_ideal_demand"][c, t]
                for c in competencies
                for t in t_covered_by_shift[t1, v1]
                if state.soft_vars["deviation_from_ideal_demand"].get((c, t))
            )
            - (20 * (len(competencies) - 1) + v1)
            for competencies in allowed_competency_combinations
            for t1, v1 in all_shifts
        }
        shift = max(shifts.items(), key=itemgetter(1))[0]        


        y_s = [
            min(
                {c: state.soft_vars["deviation_from_ideal_demand"][c, t] for c in shift[2]}.items(),
                key=itemgetter(1),
            )[0]
            for t in t_covered_by_shift[shift[0], shift[1]]
        ]
        competencies_needed = tuple(set(y_s))

        deviation_from_demand = -sum(state.soft_vars["deviation_from_ideal_demand"][c,t] for competencies_2 in allowed_competency_combinations for c in competencies_2 for t in t_covered_by_shift[shift[0], shift[1]] if (c, t) in state.soft_vars["deviation_from_ideal_demand"] if state.soft_vars["deviation_from_ideal_demand"][c,t] < 0)

        possible_employees = [(e, score) for score, e in employee_with_competency_combination[competencies_needed] if (sum(state.x[e,t,v] for t,v in shifts_at_day[int(shift[0]/24)])) == 0 if e in employees_changed]
        
        if(deviation_from_demand < 6 or max([sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks) for e, score in possible_employees]) < shift[1]):
            #print(state.soft_vars["deviation_from_ideal_demand"])
            print("RE: Deviation from demand: " + str(deviation_from_demand))
            return repair_set 

        #Initial phase to recalculate soft and hard variables of the destroyed weeks
        #Hard Restrictions/Variables
        cover_multiple_demand_periods(state, destroy_set, t_covered_by_shift, competencies)
        more_than_one_shift_per_day(state, employees_changed, demand, shifts_at_day, days)
        above_maximum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        mapping_shift_to_demand(state, destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies)
        calculate_daily_rest_error(state, daily_destroy_and_repair, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest)

        #Soft Restrictions/Variables
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        calculate_partial_weekends(state, employees_changed, shifts_at_day, saturdays)
        calculate_isolated_working_days(state, employees_changed, shifts_at_day, days)
        calculate_isolated_off_days(state, employees_changed, shifts_at_day, days)
        calculate_consecutive_days(state, employees_changed, shifts_at_day, L_C_D, days)
        calculate_weekly_rest(state, shifts_in_week, employees_changed, weeks)
        
        # below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
    
        # cover_multiple_demand_periods(state, destroy_set, t_covered_by_shift, competencies)
        # mapping_shift_to_demand(state, destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies)


        #When we have found which shift should be assigned we have to choose the employee to take this shift.
        # This time I am doing this by setting and removing instead of copy. 
        employee_objective_functions = {}
        daily_destroy = []
        for e, score in possible_employees:
            repaired = [set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1, y_s)]
            
            #Calculations needed for soft constraints to be updated after repair
            delta_calculate_negative_deviation_from_contracted_hours(state, [e], contracted_hours, weeks, time_periods_in_week, competencies, time_step)
            calculate_weekly_rest(state, shifts_in_week, [e], weeks)
            calculate_partial_weekends(state, [e], shifts_at_day, saturdays)
            calculate_isolated_working_days(state, [e], shifts_at_day, days)
            calculate_isolated_off_days(state, [e], shifts_at_day, days)
            calculate_consecutive_days(state, [e], shifts_at_day, L_C_D, days)
            #Hard restriction:
            below_minimum_demand(state, repaired, employee_with_competencies, demand, competencies, t_covered_by_shift)
            above_maximum_demand(state, repaired, employee_with_competencies, demand, competencies, t_covered_by_shift)
            more_than_one_shift_per_day(state, [e], demand, shifts_at_day, days)
            cover_multiple_demand_periods(state, repaired, t_covered_by_shift, competencies)
            mapping_shift_to_demand(state, repaired, t_covered_by_shift, shifts_overlapping_t, competencies)
            calculate_daily_rest_error(state, [daily_destroy, repaired], invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest)

            competency_score = score - len(competencies_needed)
            #Stores the objective function for this employee
            employee_objective_functions[e] = regret_objective_function(state, e, off_shifts, saturdays, days, L_C_D, weeks, contracted_hours, competencies, [shift[0]], competency_score)
            #Is needed to set the decision variable back to 0
            daily_destroy = set_x(state, t_covered_by_shift, e, shift[0], shift[1], 0, y_s)
        
        #if(len(employee_objective_functions.keys()) == 0):
         #   return repair_set

        max_value = max(employee_objective_functions.items(), key=itemgetter(1))[1]
        e = choice([key for key, value in employee_objective_functions.items() if value == max_value])

        destroy_set = [set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1, y_s)]
        repair_set.append((e, shift[0], shift[1]))
        daily_destroy_and_repair = [[], destroy_set]
