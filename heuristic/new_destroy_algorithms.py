from collections import defaultdict
from tupledict import TupleDict
from heuristic.converter import set_x
from heuristic.heuristic_calculations import calculate_isolated_working_days, calculate_partial_weekends

#Destroy and repair algorithm targeting partial weekends
def remove_partial_weekends(state, sets):
    partial_weekends = TupleDict()
    destroy_set = []
    for e,i in state.soft_vars["partial_weekends"]:
        if(state.soft_vars["partial_weekends"][e,i] != 0):
            for t,v in (sets["shifts_at_day"][i] + sets["shifts_at_day"][i+1]):
                if(state.x[e,t,v] != 0):
                    partial_weekends[e,i] = (t,v)
                    destroy_set.append((e,t,v))
                    set_x(state, sets, e,t,v,0)
    #print(partial_weekends)
    return partial_weekends, destroy_set


def remove_isolated_working_day(model):
    iso_w = calculate_isolated_working_days(model)
    iso_w_days = [key for key, value in iso_w.items() if value != 0]
    [set_x(model, e,t,v,0) for e,i in iso_w_days for t,v in model.shifts_at_day[i] if model.x[e,t,v] == 1]
    iso = defaultdict(int)
    for ele in iso_w_days:
        iso[ele[1]] += 1
    return iso