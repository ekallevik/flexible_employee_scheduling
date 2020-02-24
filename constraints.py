def cover_demand(model, employees_with_competency, competencies, shifts_work, time_periods):
#       Constraint saying the faced demand must be met. Deviation from ideal demand is penalized
#       (1.7)
        model.addConstrs((
            quicksum(
                y[c,e,t]
                for e in employees_with_competency[c])
            == demand_min[c,s,t] + mu[c,s,t] 
            for c in competencies 
            for s in shifts_work 
            for t in time_periods),
        name='minimum_demand_coverage')

#       (1.8)
        model.addConstrs((
            mu[c,s,t] <= demand_max[c,s,t] - demand_min[c,s,t]
            for c in competencies 
            for s in shifts_work 
            for t in time_periods),
        name='mu_less_than_difference')

#       (1.9)
        model.addConstrs((
            mu[c,s,t] + demand_min[c,s,t] - demand_ideal[c,s,t] 
            == delta_plus[c,s,t] - delta_minus[c,s,t] 
            for t in time_periods 
            for c in competencies
            for s in shifts_work),
        name="deviation_from_ideel_demand")

def con_mapping_shift_to_demand(model):
#       (1.10) Constraint mapping shifts to demand
    model.addConstrs((
        quicksum(
            quicksum(
                quicksum(
                    x[e,s,t_mark,v]
                    for t_mark in time_periods 
                    if t_mark >= t - v + 1 and t_mark <= t)
                for v in work_durations)
            for s in shifts_work)
        == quicksum(y[c,e,t] 
        for c in competencies) 
        for e in employees 
        for t in time_periods), 
    name="mapping_shift_to_demand")

def cover_max_one_demand(model):
#       (1.11) Constraint saying an employee cannot cover more than one requirement per time period
    model.addConstrs((
        quicksum(
            y[c,e,t] for c in competencies) <= 1  
        for e in employees 
        for t in time_periods), 
    name='max_one_demand_per_time_period')


def maximum_daily_shift(model):
#       (1.12) Constraint saying an employee can only work one shift per day.
    model.addConstrs((
        quicksum(
            quicksum(
                quicksum(
                    x[e,s,t,v] 
                    for t in time_periods 
                    if t >= ((n)*24) and t <= ((n+1)*24)) 
                for v in work_durations) 
            for s in shifts_work) <= 1 
        for n in days 
        for e in employees), 
    name="maximum_one_daily_shift")

def no_demand_cover_while_off_shift(model):
#       (1.13) Constraint making sure that employee e is not able to cover demand when allocated to an off shift.
    model.addConstrs((
        quicksum(
            quicksum(
                (1-y[c,e,t_mark])
                for t_mark in all_time_periods 
                if t_mark >= t and t_mark <= t+(v-1) and t_mark in time_periods)
            for c in competencies) >= 
                quicksum(
                1 for t_mark in all_time_periods 
                if t_mark >= t and t_mark <= t+(v-1) and t_mark in time_periods) 
                *z[e,t,v]
        for e in employees 
        for v in off_durations 
        for t in all_time_periods if t+v-1 <= max(all_time_periods)),
    name="cover_no_demand_while_off_shift")

def allocate_to_work_when_covering_demand(model):
#       (1.14) Allocate an employee to work a day if more than a number of demand is covered that day
    model.addConstrs((
        quicksum(
            quicksum(
                y[c,e,t] 
                for t in time_periods_in_day[i])
            for c in competencies)
        - L_work <= M_work_allocation * w[e,i] - 1
        for e in employees for i in days),
    name='allocated_to_work_1')

#       (1.15) 
    model.addConstrs((
        quicksum(
            quicksum(
                y[c,e,t] 
                for t in time_periods_in_day[i])
            for c in competencies)
        - L_work >= M_work_allocation * (w[e,i] - 1)
        for e in employees for i in days),
    name='allocated_to_work_2')

def minimum_daily_rest(model):
#       (1.16) Constraint saying an employee must have at least a number of continuous rest per day
    model.addConstrs((
        quicksum(
            quicksum(
                z[e,t,v] 
                for t in all_time_periods 
                if t <= offset_day_employee[e]+(n+1)*hours_in_day-v 
                and t >= offset_day_employee[e]+(n)*hours_in_day) 
            for v in daily_off_durations if v == employee_rest_daily[e]) == 1 
        for e in employees 
        for n in days), 
    name='minimum_daily_rest')

def minimum_weekly_rest(model):
#       (1.17) Constraint saying an employee must have at least a number of continuous rest per week
    model.addConstrs((
        quicksum(
            quicksum(
                z[e,t,v] 
                for t in all_time_periods 
                if t >= offset_week_employee[e]+j*hours_in_week 
                and t < offset_week_employee[e]+(j+1)*hours_in_week-(v))
            for v in weekly_off_durations 
            if v >= employee_rest_weekly[e]) == 1 
        for e in employees 
        for j in weeks), 
    name=f"minimum_weekly_rest")


def less_than_contracted_hours(model):
#       (1.18) Constraint making sure employees not exceeding contracted weekly hours.
    model.addConstrs((
        quicksum(
            quicksum(
                y[c,e,t]
                for c in competencies)
            for t in time_periods)
        + l[e] == len(weeks) * contracted_hours_employee[e]
        for e in employees),
    name="less_than_contracted_hours")   


def partial_weekends(model):
#      (1.19) If an employee work saturday or sunday it should be penalized
    model.addConstrs((
        w[e,i] - w[e,(i+1)] 
        == ro_sat[e,i] - ro_sun[e,(i+1)] 
        for e in employees 
        for i in saturdays),
    name="partial_weekends")

def backward_rotation(model):
#   (1.20) If backward rotation is happening it should be penalized
    model.addConstrs((
        quicksum(
            quicksum(
                quicksum(
                    t * x[e,s,t,v]
                    for t in time_periods_in_day[i-1])
                for s in shifts_work)
            for v in work_durations)
        -
        quicksum(
            quicksum(
                quicksum(
                    (t_marked - H_I) * x[e,s,t_marked,v]
                    for t_marked in time_periods_in_day[i])
                for s in shifts_work)
            for v in work_durations)
        <= M_I * (i) * (gamma[e,i] + 1 -
        quicksum(
            quicksum(
                quicksum(
                    x[e,s,tt,v] for tt in time_periods_in_day[i])
                for s in shifts_work)
            for v in work_durations))
        for e in employees for i in days if i > 0 
    ), name="backward_rotation")

def isolated_working_days(model):
    #   (1.19) An undesired pattern saying isolated working days should be penalized
    model.addConstrs((
        ((1-w[e,i]) + w[e,(i+1)] + (1 - w[e, (i+2)])) - L_isolated_days 
        <= M_isolated_working_day * q_iso_work[e,i] - 1
        for e in employees 
        for i in range(5)),
    name="isolated_working_day_1")

    
    model.addConstrs((
        ((1-w[e,i]) + w[e,(i+1)] + (1 - w[e, (i+2)])) - L_isolated_days
        >= M_isolated_working_day * (q_iso_work[e,i] - 1)
        for e in employees 
        for i in range(5)),
    name="isolated_working_day_2")
    
def isolated_off_days(model):
    model.addConstrs((
        (w[e,i] + (1-w[e,(i+1)]) + w[e, (i+2)]) - L_isolated_days
        <= M_isolated_working_day * q_iso_off[e,i] - 1
        for e in employees 
        for i in range(5)),
    name="isolated_off_days_1")

    model.addConstrs((
        (w[e,i] + (1-w[e,(i+1)]) + w[e, (i+2)]) - L_isolated_days
        >= M_isolated_working_day * (q_iso_off[e,i] - 1)
        for e in employees 
        for i in range(5)),
    name="isolated_off_day_2")

def consecutive_working_days(model):
#   (1.23) A soft constraint that penalized working more than a predefined number of consecutive days
    model.addConstrs((
        quicksum(
            w[e,i_marked]
            for i_marked in range(i, i+5))
        - L_consecutive_days <= M_consecutive_days * q_con[e,i] - 1
        for e in employees
        for i in range(len(days) - L_consecutive_days)),
    name="consecutive_days_1")

    model.addConstrs((
        quicksum(
            w[e,i_marked]
            for i_marked in range(i, i+5))
        - L_consecutive_days >= M_consecutive_days * (q_con[e,i] - 1)
        for e in employees
        for i in range(len(days) - L_consecutive_days)),
    name="consecutive_days_2")