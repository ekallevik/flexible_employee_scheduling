from operator import itemgetter
from collections import defaultdict
from copy import copy
from utils.const import WEEKLY_REST_DURATION
from loguru import logger


def delta_calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_repair_set):

    for c in competencies:
        for e2, t, v in destroy_repair_set:
            for t in t_covered_by_shift[t, v]:
                state.soft_vars["negative_deviation_from_demand"][c,t] = max(0,demand["ideal"][c,t] - sum(state.y[c,e,t] for e in employee_with_competencies[c]))

def calculate_deviation_from_demand(state, competencies, t_covered_by_shift, employee_with_competencies, demand, destroy_repair_set):

    for c in competencies:
        for e2, t, v in destroy_repair_set:
            for t in t_covered_by_shift[t, v]:
                if demand["ideal"].get((c, t)):
                    state.soft_vars["deviation_from_ideal_demand"][c,t] = sum(state.y[c,e,t] for e in employee_with_competencies[c]) - demand["ideal"][c,t]


def delta_calculate_negative_deviation_from_contracted_hours(state, employees, contracted_hours, weeks, time_periods_in_week, competencies, time_step):

    for e in employees:
        for j in weeks:
            state.soft_vars["deviation_contracted_hours"][e,j] = (contracted_hours[e] - sum(time_step * state.y[c,e,t]
                for c in competencies
                for t in time_periods_in_week[c, j]))

        state.hard_vars["delta_positive_contracted_hours"][e] = -min(0, sum(state.soft_vars["deviation_contracted_hours"][e,j] for j in weeks))

def calculate_weekly_rest(state, shifts_at_week, employees, weeks):
    """
    A function that calculates the longest possible weekly rest an employee can have
    based on the shifts that employee is assigned.

    If no weekly rest is possible (meaning no rest period is longer than the required number of hours)
    the hard constraint is broken and the hard variable corresponding to weekly rest gets a
    value of 1 for the week the constraint is broken.

    """
    weeks = copy(weeks)
    actual_shifts = {(e, j): [(t,v) for t,v in shifts_at_week[j] if state.x[e,t,v] == 1] for e in employees for j in weeks}
    off_shift_periods = defaultdict(list)
    weeks.append(weeks[-1] + 1)
    important = [7*24*i for i in weeks]

    for key in actual_shifts.keys():
        week = int(weeks.index(key[1]))
        if len(actual_shifts[key]) == 0:
            off_shift_periods[key] = [(important[week], float((important[week + 1] - important[week])))]

        else:
            if actual_shifts[key][0][0] - important[week] >= 36:
                off_shift_periods[key].append((important[week], actual_shifts[key][0][0] - important[week]))

            if important[week + 1] - (actual_shifts[key][-1][0] + actual_shifts[key][-1][1]) >= 36:
                off_shift_periods[key].append(((actual_shifts[key][-1][0] + actual_shifts[key][-1][1]), important[week + 1] - (actual_shifts[key][-1][0] + actual_shifts[key][-1][1])))

            for i in range(len(actual_shifts[key])-1):
                if actual_shifts[key][i + 1][0] - (actual_shifts[key][i][0] + actual_shifts[key][i][1]) >= 36:
                    off_shift_periods[key].append(((actual_shifts[key][i][0] + actual_shifts[key][i][1]), actual_shifts[key][i+1][0] - (actual_shifts[key][i][0] + actual_shifts[key][i][1])))

        if len(off_shift_periods[key]) != 0:
            state.w[key] = max(off_shift_periods[key], key=itemgetter(1))
            if key in state.hard_vars["weekly_off_shift_error"]:
                del state.hard_vars["weekly_off_shift_error"][key]
        else:
            state.hard_vars["weekly_off_shift_error"][key] = 1
            state.w[key] = (0, 0.0)



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


def calculate_f(state, employees, off_shifts, saturdays, days, L_C_D, weeks, weights):

    for e in employees:
        state.f[e] = calculate_f_for_employee(L_C_D, days, e, saturdays, state, weeks, weights)


def calculate_f_for_employee(L_C_D, days, e, saturdays, state, weeks, weights):

    f = (
        sum(
            weights["rest"] * min(WEEKLY_REST_DURATION[1], state.w[e, j][1])
            - weights["contracted hours"][e] * state.soft_vars["deviation_contracted_hours"][e, j]
            for j in weeks
        )

        - weights["partial weekends"] * sum(
            state.soft_vars["partial_weekends"][e, i]
            for i in saturdays
        )

        - sum(
            weights["isolated working days"] * state.soft_vars["isolated_working_days"][e, i + 1]
            + weights["isolated off days"] * state.soft_vars["isolated_off_days"][e, i + 1]
            for i in range(len(days) - 2)
        )

        - weights["consecutive days"] * sum(
            state.soft_vars["consecutive_days"][e, i]
            for i in range(len(days) - L_C_D)
        )
    )

    return f


def below_minimum_demand(state, repair_destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift):

    for c in competencies:
        for e2, t1, v1 in repair_destroy_set:
            for t in t_covered_by_shift[t1,v1]:
                if (c, t) in demand["min"]:
                    state.hard_vars["below_minimum_demand"][c,t] = max(0, (demand["min"][c,t] - sum(state.y[c,e,t] for e in employee_with_competencies[c])))


def above_maximum_demand(state, repair_destroy_set, employee_with_competencies, demand, competencies, t_covered_by_shift):

    for c in competencies:
        for e2, t1, v1 in repair_destroy_set:
            for t in t_covered_by_shift[t1,v1]:
                if (c, t) in demand["max"]:
                    state.hard_vars["above_maximum_demand"][c,t] = max(0, (sum(state.y[c,e,t] for e in employee_with_competencies[c]) - demand["max"][c,t]))


def more_than_one_shift_per_day(state, employees, demand, shifts_at_day, days):
    for e in employees:
        for i in days:
            state.hard_vars["more_than_one_shift_per_day"][e,i] = max(0, (sum(state.x[e,t,v] for t,v in shifts_at_day[i]) - 1))


def cover_multiple_demand_periods(state, repair_set, t_covered_by_shift, competencies):
    for e,t1,v1 in repair_set:
        for t in t_covered_by_shift[t1,v1]:
            state.hard_vars["cover_multiple_demand_periods"][e,t] = max(0,(sum(state.y[c,e,t] for c in competencies if state.y.get((c,e,t))) - 1))


# This check might not be needed if we always set y's when we set x.
def mapping_shift_to_demand(state, repair_destroy_set, t_covered_by_shift, shifts_overlapping_t, competencies):
    for e,t1,v1 in repair_destroy_set:
        for t in t_covered_by_shift[t1,v1]:
            state.hard_vars["mapping_shift_to_demand"][e,t] = max(0, abs(sum(state.x[e, t_marked, v] for t_marked, v in shifts_overlapping_t[t]) - sum(state.y[c,e,t] for c in competencies if (c,e,t) in state.y)))


def calculate_daily_rest_error(state, destroy_and_repair, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest):
    destroy = destroy_and_repair[0]
    repair = destroy_and_repair[1]

    days_in_destroy = [(e,int(t/24)) for e,t,v in destroy]

    for e, i in days_in_destroy:
        if (e, i) in state.hard_vars["daily_rest_error"]:
            del state.hard_vars["daily_rest_error"][e, i]

    for e, t, v in repair:
        i = int(t/24)

        if (t, v) in invalid_shifts[e]:
            state.hard_vars["daily_rest_error"][e, i] = 1

        if (t, v) in shift_combinations_violating_daily_rest[e]:
            value = min(1, sum(state.x[e, t1, v1]
                               for t1, v1 in shift_combinations_violating_daily_rest[e][t, v]))
            if value > 0:
                state.hard_vars["daily_rest_error"][e, i] = value
            elif (e, i) in state.hard_vars["daily_rest_error"]:
                del state.hard_vars["daily_rest_error"][e, i]

        if (t, v) in shift_sequences_violating_daily_rest[e]:
            value = max(0, sum(state.x[e, t2, v2]
                               for t2, v2 in shift_sequences_violating_daily_rest[e][t, v]) - 1)

            if value > 0:
                state.hard_vars["daily_rest_error"][e, i] = value
            elif (e, i) in state.hard_vars["daily_rest_error"]:
                del state.hard_vars["daily_rest_error"][e, i]


def hard_constraint_penalties(state):
    below_demand = sum(state.hard_vars["below_minimum_demand"].values())
    above_demand = sum(state.hard_vars["above_maximum_demand"].values())
    break_one_shift_per_day = sum(state.hard_vars["more_than_one_shift_per_day"].values())
    break_one_demand_per_time = sum(state.hard_vars["cover_multiple_demand_periods"].values())
    break_weekly_off = sum(state.hard_vars["weekly_off_shift_error"].values())
    break_shift_to_demand = sum(state.hard_vars["mapping_shift_to_demand"].values())
    break_contracted_hours = sum(state.hard_vars["delta_positive_contracted_hours"].values())

    logger.info(f"Violations: [d: ({below_demand}, {above_demand}), x: {break_one_shift_per_day}, "
                f"y: {break_one_demand_per_time}, w: {break_weekly_off}, "
                f"s-d: {break_shift_to_demand}, c: {break_contracted_hours}]")

    hard_penalties = (below_demand + above_demand + break_one_shift_per_day +
                      break_one_demand_per_time + break_weekly_off + break_shift_to_demand +
                      break_contracted_hours)

    return hard_penalties


def calculate_objective_function(state, employees, off_shifts, saturdays, L_C_D, days,
                                 weeks, weights):

    calculate_f(state, employees, off_shifts, saturdays, days, L_C_D, weeks, weights)

    g = min(state.f.values())

    penalty = 20 * hard_constraint_penalties(state)

    objective_function_value = (
            sum(state.f.values())
            + weights["lowest fairness score"] * g
            - weights["excess demand deviation factor"] * abs(sum(state.soft_vars["deviation_from_ideal_demand"].values()))
            - penalty)

    logger.info(f"Delta-objective: {objective_function_value: .2f} (incl. penalty: {penalty})")

    state.objective_function_value = objective_function_value


def calc_weekly_objective_function(state, competencies, time_periods_in_week, combined_time_periods_in_week, employees, weeks, L_C_D, k=1, setting="best", competency_score=0):

    value = {}

    for j in weeks:
        days_in_week = [i for i in range(j*7, (j+1)*7)]

        if setting == "worst":
            value[j] = (
                        sum(min(WEEKLY_REST_DURATION[1], state.w[e, j][1]) for e in employees)

                        - sum(10 * abs(state.soft_vars["deviation_from_ideal_demand"][c, t])
                              for c in competencies
                              for t in time_periods_in_week[c, j]
                              )

                        - sum(8 * state.soft_vars["partial_weekends"][e, (5 + j * 7)]
                              for e in employees
                              )

                        - sum(10 * state.soft_vars["isolated_working_days"][e, i + 1]
                              +
                              10 * state.soft_vars["isolated_off_days"][e, i + 1]
                              for e in employees
                              for i in range(len(days_in_week)-2)
                              )

                        - sum(state.soft_vars["consecutive_days"][e, i]
                              for e in employees
                              for i in range(len(days_in_week)-L_C_D)
                              )

                        - 10 * sum(state.hard_vars["below_minimum_demand"].get((c, t), 0)
                                   +
                                   state.hard_vars["above_maximum_demand"].get((c, t), 0)
                                   for c in competencies
                                   for j in weeks
                                   for t in time_periods_in_week[c, j]
                                   )

                        - 10 * sum(state.hard_vars["more_than_one_shift_per_day"].get((e, i), 0)
                                   for e in employees for i in days_in_week
                                   )

                        - 10 * sum(state.hard_vars["cover_multiple_demand_periods"].get((e, t), 0)
                                   for e in employees
                                   for j in weeks
                                   for t in combined_time_periods_in_week[j]
                                   )

                        - max(0,
                              sum(2 * state.soft_vars["deviation_contracted_hours"].get((e, j), 0)
                                  for e in employees
                                  )
                              )

                        - 10 * sum(state.hard_vars["delta_positive_contracted_hours"].get(e, 0)
                                   for e in employees
                                   )

                        - 10 * sum(state.hard_vars["daily_rest_error"].get((e, i), 0)
                                   for e in employees
                                   for i in days_in_week)
            )

        else:

            value[j] = (
                sum(min(100, state.w[e, j][1])
                    for e in employees)

                - sum(state.soft_vars["partial_weekends"][e, (5 + j * 7)]
                      for e in employees)

                - sum(state.soft_vars["isolated_working_days"][e, i + 1]
                      +
                      state.soft_vars["isolated_off_days"][e, i + 1]
                      for e in employees
                      for i in range(len(days_in_week)-2))

                - sum(state.soft_vars["consecutive_days"][e, i]
                      for e in employees
                      for i in range(len(days_in_week)-L_C_D))

                - 5 * sum(state.hard_vars["below_minimum_demand"].get((c, t), 0)
                          +
                          state.hard_vars["above_maximum_demand"].get((c, t), 0)
                          for c in competencies
                          for j in weeks
                          for t in time_periods_in_week[c, j])


                - 10 * sum(state.hard_vars["more_than_one_shift_per_day"].get((e, i), 0)
                           for e in employees
                           for i in days_in_week)

                - 10 * sum(state.hard_vars["cover_multiple_demand_periods"].get((e, t), 0)
                           for e in employees
                           for j in weeks
                           for t in combined_time_periods_in_week[j])

                - 5 * max(
                    0,
                    sum(state.soft_vars["deviation_contracted_hours"][e, j]
                        for e in employees))

                - 10 * sum(state.hard_vars["weekly_off_shift_error"].get((e, j), 0)
                           for e in employees)

                - 100 * sum(state.hard_vars["delta_positive_contracted_hours"].get(e, 0)
                            for e in employees)

                - 100 * competency_score
                - 10 * sum(state.hard_vars["daily_rest_error"].get((e, i), 0)
                           for e in employees for i in days_in_week)
                )

    if setting == "worst":
        value = sorted(value, key=value.get, reverse=False)[:k]
        return value
    else:
        return list(value.values())


def regret_objective_function(state, employee, off_shifts, saturdays, days, L_C_D, weeks, contracted_hours, competencies, t_changed, competency_score):

    return (+ sum(min(100, state.w[employee, j][1]) for j in weeks)

            + max(0, sum(state.soft_vars["deviation_contracted_hours"][employee, j]
                         for j in weeks))

            - sum(state.soft_vars["partial_weekends"][employee, i]
                  for i in saturdays)

            - sum(state.soft_vars["isolated_working_days"][employee, i+1]
                  +
                  state.soft_vars["isolated_off_days"][employee, i+1]
                  for i in range(len(days)-2))

            - sum(state.soft_vars["consecutive_days"][employee, i]
                  for i in range(len(days)-L_C_D))

            - 10 * sum(state.hard_vars["below_minimum_demand"].get((c, t), 0)
                       for c in competencies for t in t_changed)

            - 10 * sum(state.hard_vars["above_maximum_demand"].get((c, t), 0)
                       for c in competencies for t in t_changed)

            - 10 * sum(state.hard_vars["more_than_one_shift_per_day"].get((employee, i), 0)
                       for i in days)

            - 10 * sum(state.hard_vars["cover_multiple_demand_periods"].get((employee, t), 0)
                       for t in t_changed)

            - 10 * sum(state.hard_vars["weekly_off_shift_error"].get((employee, j), 0)
                       for j in weeks)

            - 10 * sum(state.hard_vars["mapping_shift_to_demand"].get((employee, t), 0)
                       for t in t_changed)

            - 10 * state.hard_vars["delta_positive_contracted_hours"].get(employee, 0)

            - 100 * competency_score
    )

"""
        What is important to calculate?
            1. deviation_from_demand vil ikke ha noe å si. Derfor unyttig å kalkulere
           
            8. Shift to demand burde ikke trenges ettersom vi sjekker om en ansatt jobber den dagen. 
            9. Cover multiple demand periods er likt den over. Burde ikke trenge å sjekkes. 
            10. More than one shift per day burde ikke trenge det heller ettersom vi sjekker et annet sted.
            11. above/below ikke nødvendig det heller. 
            
            13. Dette er opp mot objektivverdi og trenger da sannsynligvis ikke å regne egen objektivverdi. Kan bare se på hver ansatt. 
        """
"""
            2. weekly rest. Når vi setter inn et skift så bør denne kalkuleres. Bør derimot strengt tatt ikke sette verdien, men heller regne ut høyeste mulige verdi.
            3. Partial weekend vil ha noe å si hvis shiftet ble satt på en lørdag eller søndag
            4. isolated working day er vanskelig å enkelt kalkulere uten å se på dagen før og dagen etter
            5. Samme som over. Må sjekke dagen før og dagen etter.
            6. Consecutive days må sjekke strengt tatt L_C_D - 1 dager før og L_C_D -1 dager etter. 
            7. Negative deviation from contracted hours. Dette går fort å regne ut. Bare ta nåværende - varighet på skift. Alt som blir minus vil da også bryte hard restriksjon.
            12. daily_rest bør sjekkes. Bare sjekke den dagen. 
"""

def employee_shift_value(state, e, shift, saturdays, sundays, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, shifts_at_week, weeks, shifts_at_day, week, competency_score):
    day = int(shift[0]/24)
    week = int(day/7)
    daily_rest_error = regret_daily_rest_error(state, day, e, shift, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest)
    weekly_rest_error = regret_weekly_rest(state, shifts_at_week, e, week, shift)
    partial_weekend_error = regret_partial_weekend(state, e, shifts_at_day, saturdays, sundays, day)
    isolated_days_error = regret_isolated_days(state, e, shifts_at_day, day, weeks)
    deviation_contracted_hours = regret_deviation_contracted_hours(state, e, shift, week, weeks)

    return (weekly_rest_error
            + daily_rest_error  
            + partial_weekend_error 
            + isolated_days_error 
            + deviation_contracted_hours 
            - 100 * competency_score
            )



def regret_weekly_rest(state, shifts_at_week, e, week, shift):
    actual_shifts = [(t, v) for t,v in shifts_at_week[week] if state.x[e,t,v] == 1 or (t,v) == (shift[0],shift[1])]
    off_shift_periods = []
    week_interval = [7 * 24 * week, 7 * 24 * (week + 1) ]
  
    if not actual_shifts:
        off_shift_periods.append(float(week_interval[1] - week_interval[0]))
        return 0.5 * min(WEEKLY_REST_DURATION[1], off_shift_periods[0])

    else:
        if(actual_shifts[0][0] - week_interval[0] >= 36):
            off_shift_periods.append(actual_shifts[0][0] - week_interval[0])
            

        if(week_interval[1] - (actual_shifts[-1][0] + actual_shifts[-1][1]) >= 36):
            off_shift_periods.append(week_interval[1] - (actual_shifts[-1][0] + actual_shifts[-1][1]))

        for i in range(len(actual_shifts) - 1):
            if(actual_shifts[i+1][0] - (actual_shifts[i][0] + actual_shifts[i][1]) >= 36):
                off_shift_periods.append(actual_shifts[i+1][0] - (actual_shifts[i][0] + actual_shifts[i][1]))

    if off_shift_periods:
        return 0.5 * min(WEEKLY_REST_DURATION[1], max(off_shift_periods))
    
    return -200


def regret_partial_weekend(state, e, shifts_at_day, saturdays, sundays, day):
    if day in saturdays:
        if sum(state.x[e, t, v] for t,v in shifts_at_day[day + 1]) == 0:
            return -50

    elif day in sundays:
        if sum(state.x[e, t, v] for t,v in shifts_at_day[day - 1]) == 0:
            return -50
    return 0


def regret_isolated_days(state, e, shifts_at_day, day, weeks):
    isolated_day = 0

    if 1 < day < len(weeks)*7-2:
    
    #Isolated Working Day
        if sum(state.x[e,t,v] for t,v in (shifts_at_day[day - 1] + shifts_at_day[day + 1])) == 0:
            isolated_day += 1
        
        #Isolated off day
        if sum(1 for t,v in shifts_at_day[day - 2] if state.x.get((e,t,v))) == 1:
            if sum(1 for t,v in shifts_at_day[day - 1] if state.x.get((e,t,v))) == 0 :
                isolated_day += 1
        
        if sum(1 for t,v in shifts_at_day[day + 2] if state.x.get((e,t,v))) == 1:
            if sum(1 for t,v in shifts_at_day[day + 1] if state.x.get((e,t,v))) == 0 :
                isolated_day += 1
        
        return 10 * -isolated_day

    else:
        return 0

def regret_deviation_contracted_hours(state, e, shift, j, weeks):
    negative_deviation_from_contracted_hours = state.soft_vars["deviation_contracted_hours"][e,j] - shift[1]
    total_negative_deviation_from_contracted_hours = sum(state.soft_vars["deviation_contracted_hours"][e,j_2] for j_2 in weeks) - shift[1]
    if total_negative_deviation_from_contracted_hours < 0:
        #Remeber that this is negative to begin with. The other two are positive
        return 100 * total_negative_deviation_from_contracted_hours
    elif total_negative_deviation_from_contracted_hours == 0:
        return 200
    return 1.5 * negative_deviation_from_contracted_hours


def regret_daily_rest_error(state, day, e, shift, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest):
    if shift in invalid_shifts[e]:
        return -100
    elif shift in shift_combinations_violating_daily_rest[e]:
        return -100 * min(1, sum(state.x[e, t1, v1] for t1, v1 in shift_combinations_violating_daily_rest[e][shift[0], shift[1]]))
    elif shift in shift_sequences_violating_daily_rest[e]:
        return -100 * max(0, sum(state.x[e, t2, v2] for t2, v2 in shift_sequences_violating_daily_rest[e][shift[0], shift[1]]) - 1)
    else:
        return 0

# def calculate_consecutive_days(state, e, shifts_at_day, L_C_D, day):
#         for i in range(len(days)-L_C_D):
#             state.soft_vars["consecutive_days"][e,i] = max(0,(sum(sum(state.x[e,t,v] for t,v in shifts_at_day[i_marked]) for i_marked in range(i, i+L_C_D)))- L_C_D)



def worst_employee_regret_value(state, e, shift, saturdays, sundays, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest, shifts_at_week, weeks, shifts_at_day, days, competency_score):
    day = int(shift[0]/24)
    week = int(day/7)

    daily_rest_error = regret_daily_rest_error(state, day, e, shift, invalid_shifts, shift_combinations_violating_daily_rest, shift_sequences_violating_daily_rest)
    weekly_rest_other_weeks = sum(state.w[e,j][1] for j in weeks if j != week)
    isolated_off_days_other_weeks = sum(state.soft_vars["isolated_off_days"][e,i+1] + state.soft_vars["isolated_working_days"][e,i+1] for i in range(len(days)-2))
    partial_weekends_other_weeks = sum(state.soft_vars["partial_weekends"][e,i] for i in saturdays)

    total_negative_deviation_from_contracted_hours = sum(state.soft_vars["deviation_contracted_hours"][e,j_2] for j_2 in weeks) - shift[1]
    
    
    if total_negative_deviation_from_contracted_hours < 0:
        contracted_hours = 5 * total_negative_deviation_from_contracted_hours
    elif total_negative_deviation_from_contracted_hours == 0:
        contracted_hours = 100
    else:
        contracted_hours = total_negative_deviation_from_contracted_hours

    current_week_rest = regret_weekly_rest(state, shifts_at_week, e, week, shift)
    current_isolated_days = regret_isolated_days(state, e, shifts_at_day, day, weeks)
    current_partial_weekends = regret_partial_weekend(state, e, shifts_at_day, saturdays, sundays, day)

    return (
            current_week_rest
            + daily_rest_error
            + contracted_hours
            + current_isolated_days
            + current_partial_weekends #* (-partial_weekends_other_weeks)
            #weekly_rest_other_weeks
            #isolated_off_days_other_weeks
            
    )

"""
    Forskjell når man ser på en ansatt:
    2. isolated_days. Burde egentlig sjekke gjennom alle mulige isolated_days for å spre dem jevnt ut.
    3. samme gjelder med partial weekends. Man burde se alle partial weekend å ta det med inn i beregningen for hvem som skal få en til
    4. Weekly_rest. Kan her bare telle over en ansatt sine andre i tilegg til å gjøre den testen over. Hvor mye man får i en uke er jo viktig. 
    5. kontraktsfestede timer burde gå over hele perioden istedenfor for bare en uke. 
"""
