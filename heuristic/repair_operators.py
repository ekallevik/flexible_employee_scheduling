from heuristic.delta_calculations import delta_calculate_deviation_from_demand, delta_calculate_negative_deviation_from_contracted_hours
from operator import itemgetter
from heuristic.converter import set_x

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