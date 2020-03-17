from hard_constraint_model_class import *
from xml_loader.shift_generation import load_data, get_t_covered_by_shift

problem_name = "rproblem3"
data_folder = Path(__file__).resolve().parents[1] / 'flexible_employee_scheduling_data/xml data/Real Instances/'
root = ET.parse(data_folder / (problem_name + '.xml')).getroot()

model = Optimization_model(problem_name)
model.add_variables()
model.add_constraints()
model.set_objective()
model.optimize()

x = model.x
y = model.y
w = model.w

# for e in model.employees:
#     for t,v in model.off_shifts:
#         if(w[e,t,v].x == 1):
#             print(e,t,v)
def calculate_deviation_from_demand():
    delta = {}
    for c in model.competencies:
        for t in model.time_periods:
            delta[c,t] = abs(sum(model.y[c,e,t].x for e in model.employee_with_competencies[c]) - model.demand["ideal"][c,t])
            # if(delta[c,t] - abs(model.delta["plus"][c,t].x - model.delta["minus"][c,t].x)) != 0:
            #     print(delta[c,t] - abs(model.delta["plus"][c,t].x - model.delta["minus"][c,t].x))
            #     print("Different Delta")
    return delta

def calculate_deviation_from_contracted_hours():
    delta_contracted_hours = {}
    for e in model.employees:
        delta_contracted_hours[e] = (len(model.weeks) * model.contracted_hours[e] - sum(
            sum(
                model.time_step * y[c,e,t].x for t in model.time_periods
            ) for c in model.competencies
        ))
    return delta_contracted_hours

def calculate_partial_weekends():
    partial_weekend = {}
    print("Partial Weekends")
    for e in model.employees:
        for i in model.saturdays:
            partial_weekend[e,i] = abs((sum(model.x[e,t,v].x for t,v in model.shifts_at_day[i]) - sum(model.x[e,t,v].x for t,v in model.shifts_at_day[i+1])))
            # if(partial_weekend[e,i] != abs(model.ro["sat"][e,i].x - model.ro["sun"][e,(i+1)].x)):
            #     print(str(partial_weekend) + "," + str(abs(model.ro["sat"][e,i].x - model.ro["sun"][e,(i+1)].x)))
            #     print(i)
            #     print("Different partial weekends")
    return partial_weekend

def calculate_isolated_working_days():
    isolated_working_days = {}
    for e in model.employees:
        for i in range(len(model.days)-2):
            isolated_working_days[e,i] = max(0,(-sum(x[e,t,v].x for t,v in model.shifts_at_day[i]) 
            + sum(x[e,t,v].x for t,v in model.shifts_at_day[i+1]) 
            - sum(x[e,t,v].x for t,v in model.shifts_at_day[i+2])))

            # if(isolated_working_days[e,i] != model.q_iso["work"][e,i].x):
            #     print("Different isolated working days")

    return isolated_working_days


def calculate_isolated_off_days():
    isolated_off_days = {}
    for e in model.employees:
        for i in range(len(model.days)-2):
            isolated_off_days[e,i+1] = max(0,(sum(x[e,t,v].x for t,v in model.shifts_at_day[i]) 
            - sum(x[e,t,v].x for t,v in model.shifts_at_day[i+1]) 
            + sum(x[e,t,v].x for t,v in model.shifts_at_day[i+2])-1))
        # if(isolated_off_days[e,i] != model.q_iso["off"][e,i].x):
        #     print("Different isolated off days")
    return isolated_off_days

def calculate_consecutive_days():
    consecutive_days = {}
    for e in model.employees:
        for i in range(len(model.days)-model.L_C_D):
            consecutive_days[e,i] = max(0,(sum(
                sum(x[e,t,v].x for t,v in model.shifts_at_day[i_marked]) 
            for i_marked in range(i,i+model.L_C_D)))- model.L_C_D)
            
            # if(consecutive_days[e,i] != model.q_con[e,i].x):
            #     print("Different consecutive days")
    return consecutive_days

def calculate_objective_function():
    partial_weekend = calculate_partial_weekends()
    q_iso_work = calculate_isolated_working_days()
    q_iso_off = calculate_isolated_off_days()
    q_con = calculate_consecutive_days()
    delta = calculate_deviation_from_demand()
    delta_c = calculate_deviation_from_contracted_hours()
    lowest_contracted_hours(delta_c, delta)
   # for e in model.employees:
    #    print(str(delta_c[e]) + ", index: " + str(e)) 
    f = {}
    for e in model.employees:
        f[e] = (sum(v * w[e,t,v].x for t,v in model.off_shifts)
            - delta_c[e]
            - sum(partial_weekend[e,i] for i in model.saturdays)
            - sum(q_iso_work[e,i] for i in range(len(model.days)-2))
            - sum(q_iso_off[e,i+1] for i in range(len(model.days)-2))
            - sum(q_con[e,i] for i in range(len(model.days)-model.L_C_D)))
        #print(str(f[e]) + ", " + str(model.f["plus"][e].x-model.f["minus"][e].x) + ", index: "+ str(e))
    g = min(f.values())

    objective =    (sum(f[e] for e in model.employees)
                    + g
                    - sum(sum(delta[c,t] for t in model.time_periods) for c in model.competencies)
                    )

    #print(objective)
def cover_minimum_demand():
    below_minimum_demand = {}
    for c in model.competencies:
        for t in model.time_periods:
            below_minimum_demand[c,t] = max(0, (model.demand["min"][c,t] - sum(y[c,e,t].x for e in model.employee_with_competencies[c])))

def under_maximum_demand():
    above_maximum_demand = {}
    for c in model.competencies:
        for t in model.time_periods:
            above_maximum_demand[c,t] = max(0, (sum(y[c,e,t].x for e in model.employee_with_competencies[c]) - model.demand["max"][c,t]))

def maximum_one_shift_per_day():
    more_than_one_shift_per_day = {}
    for e in model.employees:
        for i in model.days:
            more_than_one_shift_per_day[e,i] = max(0, (sum(x[e,t,v].x for t,v in model.shifts_at_day[i]) - 1))

def cover_only_one_demand_per_time_period():
    cover_multiple_demand_periods = {}
    for e in model.employees:
        for t in model.time_periods:
            cover_multiple_demand_periods[e,t] = max(0,(sum(y[c,e,t].x for c in model.competencies) - 1))

def one_weekly_off_shift():
    weekly_off_shift_error = {}
    for e in model.employees:
        for j in model.weeks:
            weekly_off_shift_error[e,j] = max(0,(abs(sum(w[e,t,v].x for t,v in model.off_shift_in_week[j]) - 1)))

def no_work_during_off_shift():
    no_work_during_off_shift = {}
    for e in model.employees:
        for t,v in model.off_shifts:
           no_work_during_off_shift[e,t,v] = max(0,(len(model.shifts_covered_by_off_shift[t,v]) * model.w[e,t,v].x) - sum((1 - x[e,t_marked, v_marked].x) for t_marked, v_marked in model.shifts_covered_by_off_shift[t,v]))


def mapping_shift_to_demand():
    mapping_shift_to_demand = {}
    for e in model.employees:
        for t in model.time_periods:
           mapping_shift_to_demand[e,t] = max(0,abs(sum(model.x[e, t_marked, v].x for t_marked, v in model.shifts_overlapping_t[t]) - sum(model.y[c,e,t].x for c in model.competencies)))

#Repair algorithms:
def lowest_contracted_hours(delta_c, delta):
    employee = min(delta_c, key=delta_c.get)
    working_days = []
    t = get_t_covered_by_shift(root)
    for i in model.days:
        if sum(model.x[employee,t,v].x for t,v in model.shifts_at_day[i]) != 0:
            working_days.append(i)
    print(working_days)
    maximum_deviation_from_demand = {}
    for i in working_days:
        for shift in model.shifts_at_day[i]:
            maximum_deviation_from_demand[shift] = sum(delta[0,t] for t in t[shift])
   # placement = max(maximum_deviation_from_demand, key=maximum_deviation_from_demand.get)
   # print(x[employee, placement[0], placement[1]].set(1))
   # delta2 = calculate_deviation_from_contracted_hours()
   # print(employee)
   # print(min(delta2, key=delta2.get))

















# cover_minimum_demand()
# under_maximum_demand()
# maximum_one_shift_per_day()
# cover_only_one_demand_per_time_period()
# one_weekly_off_shift()
# no_work_during_off_shift()
# mapping_shift_to_demand()

# no_work_during_off_shift()
calculate_objective_function()

