from gurobipy import *


def add_y(model, sets):
    return model.addVars(
        sets["competencies"],
        sets["employees"]["all"],
        sets["time"]["periods"],
        vtype=GRB.BINARY,
        name="y",
    )


def add_x(model, sets):
    return model.addVars(
        sets["employees"]["all"], sets["shifts"]["shifts"], vtype=GRB.BINARY, name="x"
    )


def add_w(model, sets):
    return model.addVars(
        sets["employees"]["all"], sets["shifts"]["off_shifts"], vtype=GRB.BINARY, name="w"
    )


def add_mu(model, sets):
    return model.addVars(
        sets["competencies"], sets["time"]["periods"], vtype=GRB.INTEGER, name="mu"
    )


def add_delta(model, sets):

    delta = {
        "plus": model.addVars(
            sets["competencies"], sets["time"]["periods"], vtype=GRB.INTEGER, name="delta_plus"
        ),
        "minus": model.addVars(
            sets["competencies"], sets["time"]["periods"], vtype=GRB.INTEGER, name="delta_minus"
        ),
    }

    return delta


def add_gamma(model, sets):
    return model.addVars(sets["employees"], sets["time"]["days"], vtype=GRB.BINARY, name="gamma")


def add_lambda(model, sets):
    return model.addVars(sets["employees"], vtype=GRB.CONTINUOUS, name="lambda")


def add_rho(model, sets):

    rho = {
        "sat": model.addVars(sets["employees"], sets["time"]["days"], vtype=GRB.BINARY, name="rho_sat"),
        "sun": model.addVars(sets["employees"], sets["time"]["days"], vtype=GRB.BINARY, name="rho_sun"),
    }

    return rho


def add_q(model, sets):

    q = {
        "iso_off": model.addVars(
            sets["employees"], sets["time"]["days"], vtype=GRB.BINARY, name="q_iso_off"
        ),
        "iso_work": model.addVars(
            sets["employees"], sets["time"]["days"], vtype=GRB.BINARY, name="q_iso_work"
        ),
        "con": model.addVars(sets["employees"], sets["time"]["days"], vtype=GRB.BINARY, name="q_con"),
    }

    return q


def add_f(model, sets):

    f = {
        "plus": model.addVars(sets["employees"], vtype=GRB.CONTINUOUS, name="f_plus"),
        "minus": model.addVars(sets["employees"], vtype=GRB.CONTINUOUS, name="f_minus"),
    }

    return f


def add_g(model):

    g = {
        "plus": model.addVar(vtype=GRB.CONTINUOUS, name="g_plus"),
        "minus": model.addVar(vtype=GRB.CONTINUOUS, name="g_minus"),
    }

    return g


def add_variables(model, sets):

    variables = {
        "y": add_y(model, sets),
        "x": add_x(model, sets),
        "w": add_w(model, sets),
        "mu": add_mu(model, sets),
        "delta": add_delta(model, sets),
        "gamma": add_gamma(model, sets),
        "lam": add_lambda(model, sets),
        "rho": add_rho(model, sets),
        "q": add_q(model, sets),
        "f": add_f(model, sets),
        "g": add_g(model),
    }

    return variables
