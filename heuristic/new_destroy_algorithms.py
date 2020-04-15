from collections import defaultdict
from tupledict import TupleDict
from heuristic.converter import set_x
from heuristic.heuristic_calculations import calculate_isolated_working_days, calculate_partial_weekends

#Destroy and repair algorithm targeting partial weekends
def remove_partial_weekends(state, sets):
    partial_weekends = defaultdict(list)
    destroy_set = []
    for e,i in state.soft_vars["partial_weekends"]:
        if(state.soft_vars["partial_weekends"][e,i] != 0):
            for t,v in (sets["shifts_at_day"][i] + sets["shifts_at_day"][i+1]):
                if(state.x[e,t,v] != 0):
                    partial_weekends[i].append((e,t,v))
                    destroy_set.append((e,t,v))
                    set_x(state, sets, e,t,v,0)
    return partial_weekends, destroy_set


def remove_isolated_working_day(state, sets):
    iso_w_days = [key for key, value in state.soft_vars["isolated_working_days"].items() if value != 0]
    destroy_set = [set_x(state, sets, e, t, v, 0) for e, i in iso_w_days for t,v in sets["shifts_at_day"][i] if state.x[e,t,v] == 1]
    iso = defaultdict(int)
    for ele in iso_w_days:
        iso[ele[1]] += 1
    return iso, destroy_set


"""
    Possible destroy operators to be explored:
    Spesific:
        1.  Remove isolated working days. A number of isolated working days are removed. This could be done either greedily, randomly or overall.
            By doing this we remove the penalization from having isolated working days. Based on having an isolated working day we know that
            we now have three possible days to place an employee. 

        2.  Remove isolated off days. This could as with isolated working days be done greedily, randomly or overall. To remove an isolated off day
            we would have to either give the employee a shift on the isolated day, remove the day after or the day before the isolated working day. 
            By placing a shift we increase number of working hours, possibly breaking contracted hours. 
            By removing either the day before or next day we get a possibility to place an off shift in between. In addition we would more likely not 
            break contracted hours. 

        3.  Remove consecutive days. If an employee have more than a predefined number of working days in a row we would penalize the employee. 
            If this happens we would have to remove either the first day in the row, the last or any number of days in between to break up the consecutive days.
            If we remove a single day in between we would end up with an isolated off day which is not ideal. 
            If we remove a number of days we would decrease number of working hours. We would have to place shift other places.
            If we remove the first or last day we would decrease working hours. Would most likely have to place a shift on another day.

        4.  Remove parts of the solution that are breaking hard constraints in hope of creating a legal solution. An example are breaking contracted
            hours. This is not easily fixed by a general or spesific destroy/repair operator as they mostly try to increase working hours to 
            a maximum. Would here look at how much it is breaking it and greedly remove the shift that gives the least to the solution. 

    General:
        1.  Worst removal: Try to remove the worst part of the solution. How to define this is difficult. We would have to do many calculations
            to find out which part is worst. In our case we would for every shift placed we would have to remove the shift and see how this affects
            the solution. We would choose a number of shifts to remove depending on a destruction criteria. Further calculations would possibly have
            to be done in order to find the second worst and so on. To repair we could do a number of different general repairs.
            
            Another adaption of this could be to remove parts of the solution that are worst, but not calculating every aspect of the solution.
            This could be only looking at the worst f. 
        
        2. Random removal. Just remove random shifts and off shifts from the solution. No calculations are needed.
"""