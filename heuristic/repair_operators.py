from heuristic.delta_calculations import delta_calculate_deviation_from_demand, delta_calculate_negative_deviation_from_contracted_hours, calculate_weekly_rest, calculate_partial_weekends, calculate_isolated_working_days, calculate_isolated_off_days, calculate_consecutive_days, calc_weekly_objective_function, cover_multiple_demand_periods, more_than_one_shift_per_day, above_maximum_demand, below_minimum_demand
from heuristic.delta_calculations import delta_calculate_deviation_from_demand, delta_calculate_negative_deviation_from_contracted_hours, regret_objective_function, calculate_weekly_rest, calculate_partial_weekends, calculate_isolated_working_days, calculate_isolated_off_days, calculate_consecutive_days, below_minimum_demand, above_maximum_demand, more_than_one_shift_per_day, cover_multiple_demand_periods, mapping_shift_to_demand
from operator import itemgetter
from heuristic.converter import set_x
from copy import copy

def worst_week_repair(state, week, shifts_in_week, competencies, destroy_set, t_covered_by_shift, employee_with_competencies, demand, time_step, time_periods_in_week, employees, contracted_hours, weeks, shifts_at_day):
    repair_set = []
    employees_changed = employees
    changed = destroy_set

    while(True):
        delta_calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, changed)
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)
        deviation_from_demand = sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in competencies for t in time_periods_in_week[week[0]])
        
        if(deviation_from_demand < 6):
            #print([state.soft_vars["negative_deviation_from_demand"][c,t] for c in competencies for t in time_periods_in_week[week[0]]])
            #print(deviation_from_demand)
            return repair_set

        shifts = {(t1, v1): sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in competencies for t in t_covered_by_shift[t1, v1]) - v1 for t1, v1 in shifts_in_week[week[0]]}
        shift = max(shifts.items(), key=itemgetter(1))[0]
        #print([state.soft_vars["negative_deviation_from_demand"][c,t] for c in competencies for t in time_periods_in_week[week[0]]])
        deviaton_contracted_hours = {e: sum(state.soft_vars["contracted_hours"][e,j] for j in week) for e in employees if (sum(state.x[e,t,v] for t,v in shifts_at_day[int(shift[0]/24)])) == 0}
       # state.x[e,shift[0],shift[1]] != 1}
        e = max(deviaton_contracted_hours.items(), key=itemgetter(1))[0]

        repair_set.append(set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1))
        employees_changed = [e]
        changed = [(e, shift[0], shift[1])]

def worst_week_regret_repair(state, week, shifts_in_week, competencies, destroy_set, t_covered_by_shift, employee_with_competencies, demand, time_step, time_periods_in_week, employees, contracted_hours, weeks, shifts_at_day, L_C_D):
    repair_set = []
    employees_changed = employees
    destroy_set = destroy_set
    saturdays = [5 + j * 7 for j in week]
    days = [i + (7 * j) for j in week for i in range(7)]
    while(True):
        #Initial phase to recalculate soft variables of the destroyed weekend
        delta_calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)
        calculate_weekly_rest(state, shifts_in_week, employees_changed, copy(week))
        #calculate_partial_weekends(state, employees_changed, shifts_at_day, saturdays)
        #calculate_isolated_working_days(state, employees_changed, shifts_at_day, days)
        #calculate_isolated_off_days(state, employees_changed, shifts_at_day, days)
        #calculate_consecutive_days(state, employees_changed, shifts_at_day, L_C_D, days)
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)

        cover_multiple_demand_periods(state, repair_set, t_covered_by_shift, competencies)
        more_than_one_shift_per_day(state, destroy_set, demand, shifts_at_day, days)
        above_maximum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)

        deviation_from_demand = sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in competencies for t in time_periods_in_week[week[0]])
        
        if(deviation_from_demand < 6):
            #print([state.soft_vars["negative_deviation_from_demand"][c,t] for c in competencies for t in time_periods_in_week[week[0]]])
            #print(deviation_from_demand)
            return repair_set
        #Chooses the shift with highest deviation from demand
        shifts = {(t1, v1): sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in competencies for t in t_covered_by_shift[t1, v1]) - v1 for t1, v1 in shifts_in_week[week[0]]}
        shift = max(shifts.items(), key=itemgetter(1))[0]

        #Now we have to decide on which employee should be assigned this shift. 
        #Since we want to do this through regret we have to calculate the objective function of the state with that shift taken for each employee. 
        #We have two options here: 
        # 1. We could copy the state we are working with. We would have to use deepcopy which takes time and resources.
        # 2. We could set the x value and then remove it again after calculation. Might take a lot of time and resources. 

        #Deepcopy method:
        possible_employees = [e for e in employees if (sum(state.x[e,t,v] for t,v in shifts_at_day[int(shift[0]/24)])) == 0]
        objective_values = {}
        for e in possible_employees:
            current_state = state.copy()
            set_x(current_state, t_covered_by_shift, e, shift[0], shift[1], 1)

            #Soft restriction calculations
            delta_calculate_deviation_from_demand(current_state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)
            calculate_weekly_rest(current_state, shifts_in_week, [e], copy(week))
            calculate_partial_weekends(current_state, [e], shifts_at_day, saturdays)
            calculate_isolated_working_days(current_state, [e], shifts_at_day, days)
            calculate_isolated_off_days(current_state, [e], shifts_at_day, days)
            calculate_consecutive_days(current_state, [e], shifts_at_day, L_C_D, days)
            delta_calculate_negative_deviation_from_contracted_hours(current_state, [e], contracted_hours, weeks, time_periods_in_week, competencies, time_step)
            
            #Hard constraint calculations
            #mapping_shift_to_demand(state, destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies)
            cover_multiple_demand_periods(state, repair_set, t_covered_by_shift, competencies)
            more_than_one_shift_per_day(current_state, destroy_set, demand, shifts_at_day, days)
            above_maximum_demand(current_state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
            below_minimum_demand(current_state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)

            objective_values[e] = calc_weekly_objective_function(current_state, competencies, time_periods_in_week, employees, week, L_C_D, 1)
            #current_state.write("heuristic_solution" + str(e))
        print(objective_values)
        employee = max(objective_values.items(), key=itemgetter(1))[0]
        print(employee)
        
        repair_set.append(set_x(state, t_covered_by_shift, employee, shift[0], shift[1], 1))
        employees_changed = [employee]
        destroy_set = [(employee, shift[0], shift[1])]

def worst_employee_repair(state, destroy_set, employees, competencies, t_covered_by_shift, employee_with_competencies, demand, contracted_hours, weeks, time_periods_in_week, time_step, all_shifts, shifts_at_day):
    repair_set = []
    destroy_set = destroy_set
    employees_changed = employees
    
    for i in range(65):
        delta_calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)
        delta_calculate_negative_deviation_from_contracted_hours(state, employees_changed, contracted_hours, weeks, time_periods_in_week, competencies, time_step)

        shifts = {(t1, v1): sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in competencies for t in t_covered_by_shift[t1, v1]) - v1 for t1, v1 in all_shifts}
        shift = max(shifts.items(), key=itemgetter(1))[0]

        deviation_from_demand = sum(state.soft_vars["negative_deviation_from_demand"].values())

        if(deviation_from_demand < 6):
            return repair_set

        deviaton_contracted_hours = {e: sum(state.soft_vars["contracted_hours"][e,j] for j in weeks) for e in employees if (sum(state.x[e,t,v] for t,v in shifts_at_day[int(shift[0]/24)])) == 0}
        print(deviaton_contracted_hours)
        e = max(deviaton_contracted_hours.items(), key=itemgetter(1))[0]

        repair_set.append(set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1))
        employees_changed = [e]
        destroy_set = [(e, shift[0], shift[1])]

def worst_employee_regret_repair(state, destroy_set, employees_changed, competencies, t_covered_by_shift, employee_with_competencies, demand, all_shifts, off_shifts, saturdays, days, L_C_D, weeks, shifts_at_day, shifts_at_week, contracted_hours, time_periods_in_week, time_step, shifts_overlapping_t):
    repair_set = []
    destroy_set = destroy_set
    employee = employees_changed

    for i in range(100):
        delta_calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_set)
        shifts = {(t1, v1): sum(state.soft_vars["negative_deviation_from_demand"][c,t] for c in competencies for t in t_covered_by_shift[t1, v1]) - v1 for t1, v1 in all_shifts}
        shift = max(shifts.items(), key=itemgetter(1))[0]

        deviation_from_demand = sum(state.soft_vars["negative_deviation_from_demand"].values())
        #print(deviation_from_demand)
        if(deviation_from_demand < 6):
            return repair_set
        below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        above_maximum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
        cover_multiple_demand_periods(state, destroy_set, t_covered_by_shift, competencies)
        mapping_shift_to_demand(state, destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies)


        #When we have found which shift should be assigned we have to choose the employee to take this shift.
        # This time I am doing this by setting and removing instead of deepcopy. 

        possible_employees = [e for e in employees_changed if (sum(state.x[e,t,v] for t,v in shifts_at_day[int(shift[0]/24)])) == 0]
        employee_objective_functions = {}
        for e in possible_employees:
            destroy_set = [set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1)]
            
            #Calculations needed for soft constraints to be updated after destroy
            #Needed to calculate the new deviation from demand
            delta_calculate_negative_deviation_from_contracted_hours(state, [e], contracted_hours, weeks, time_periods_in_week, competencies, time_step)
            #Needed to calculate the new weekly rest for the employees that have had their weeks removed
            calculate_weekly_rest(state, shifts_at_week, [e], weeks)
            #Partial weekends should be updated as well
            calculate_partial_weekends(state, [e], shifts_at_day, saturdays)
            #Isolated working days
            calculate_isolated_working_days(state, [e], shifts_at_day, days)
            #isolated off days
            calculate_isolated_off_days(state, [e], shifts_at_day, days)
            #Consecutive days
            calculate_consecutive_days(state, [e], shifts_at_day, L_C_D, days)
            
            
            #Hard restriction:
            below_minimum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
            above_maximum_demand(state, destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift)
            more_than_one_shift_per_day(state, [e], demand, shifts_at_day, days)
            cover_multiple_demand_periods(state, destroy_set, t_covered_by_shift, competencies)
            mapping_shift_to_demand(state, destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies)

            employee_objective_functions[e] = regret_objective_function(state, e, off_shifts, saturdays, days, L_C_D, weeks, contracted_hours, competencies, [shift[0]])
            set_x(state, t_covered_by_shift, e, shift[0], shift[1], 0)
        

        e = max(employee_objective_functions.items(), key=itemgetter(1))[0]
        #print(employee_objective_functions)
        #print(e)
        destroy_set = [set_x(state, t_covered_by_shift, e, shift[0], shift[1], 1)]
        repair_set.append((e, shift[0], shift[1]))
        #state.write("heuristic_regret_solution")
