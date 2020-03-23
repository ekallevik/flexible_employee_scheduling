def convert(model):
    x = {(e,t,v): abs(model.x[e,t,v].x) for e,t,v in model.x}
    y = {(c,e,t): abs(model.y[c,e,t].x) for c,e,t in model.y}
    w = {(e,t,v): abs(model.w[e,t,v].x) for e,t,v in model.w}
    return x,y,w


def set_x(model, e, t, v, value):
    model.x[e,t,v] = value
    #Need a smarter solution for choosing competency
    for t in model.t_covered_by_shift[t,v]:
        model.y[0,e,t] = value