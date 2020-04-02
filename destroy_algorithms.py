from collections import defaultdict
from converter import set_x
from heuristic_calculations import calculate_isolated_working_days, calculate_partial_weekends

#Destroy and repair algorithm targeting partial weekends
def remove_partial_weekends(model):
    partial_weekends = calculate_partial_weekends(model)
    for e,t,v in partial_weekends[1]:
        set_x(model, e,t,v,0)
    return partial_weekends



def remove_isolated_working_day(model):
    iso_w = calculate_isolated_working_days(model)
    iso_w_days = [key for key, value in iso_w.items() if value != 0]
    [set_x(model, e,t,v,0) for e,i in iso_w_days for t,v in model.shifts_at_day[i] if model.x[e,t,v] == 1]
    iso = defaultdict(int)
    for ele in iso_w_days:
        iso[ele[1]] += 1
    return iso