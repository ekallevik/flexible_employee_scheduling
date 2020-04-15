from tupledict import TupleDict

def convert(model):
    x = {(e,t,v): abs(model.x[e,t,v].x) for e,t,v in model.x}
    y = {(c,e,t): abs(model.y[c,e,t].x) for c,e,t in model.y}
    w = {(e,t,v): abs(model.w[e,t,v].x) for e,t,v in model.w}
    return x,y,w


def set_x(state, sets, e, t, v, value):
    state.x[e,t,v] = value
    #Need a smarter solution for choosing competency
    for t1 in sets["t_covered_by_shift"][t,v]:
        state.y[0,e,t1] = value
    return (e,t,v)
