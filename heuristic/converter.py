
def convert(model):
    x = {(e,t,v): abs(model.x[e,t,v].x) for e,t,v in model.x}
    y = {(c,e,t): abs(model.y[c,e,t].x) for c,e,t in model.y}
    w = {(e,j): (t,v) for e in model.employees for j in model.weeks for t,v in model.off_shift_in_week[j] if model.w[e,t,v].x == 1}
    return x,y,w


def set_x(state, t_covered_by_shift, e, t, v, value, y_s=None):
    state.x[e,t,v] = value
    #Need a smarter solution for choosing competency
    if y_s == None:
        for t1 in t_covered_by_shift[t,v]:
            state.y[0,e,t1] = value
    else:
        for t1, c in zip(t_covered_by_shift[t,v], y_s):
            state.y[c,e,t1] = value

    return (e,t,v)


def remove_x(state, t_covered_by_shift, competencies, e, t, v):
    state.x[e,t,v] = 0
    for t1 in t_covered_by_shift[t,v]:
        for c in competencies:
            state.y[c,e,t1] = 0
    return (e,t,v)