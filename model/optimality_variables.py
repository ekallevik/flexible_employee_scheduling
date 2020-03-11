from gurobipy import *

from model.base_variables import BaseVariables


class OptimalityVariables(BaseVariables):
    def __init__(self, model, sets):
        super(OptimalityVariables, self).__init__(model, sets)

        self.rho = self.add_rho(sets)
        self.q = self.add_q(sets)
        self.gamma = self.add_gamma(sets)
        self.f = self.add_f(sets)
        self.g = self.add_g(sets)

    def add_rho(self, sets):

        rho = {
            "sat": self.model.addVars(
                sets["employees"]["all"], sets["time"]["days"], vtype=GRB.BINARY, name="rho_sat"
            ),
            "sun": self.model.addVars(
                sets["employees"]["all"], sets["time"]["days"], vtype=GRB.BINARY, name="rho_sun"
            ),
        }

        return rho

    def add_q(self, sets):

        q = {
            "iso_off": self.model.addVars(
                sets["employees"]["all"], sets["time"]["days"], vtype=GRB.BINARY, name="q_iso_off"
            ),
            "iso_work": self.model.addVars(
                sets["employees"]["all"], sets["time"]["days"], vtype=GRB.BINARY, name="q_iso_work"
            ),
            "con": self.model.addVars(
                sets["employees"]["all"], sets["time"]["days"], vtype=GRB.BINARY, name="q_con"
            ),
        }

        return q

    def add_f(self, sets):

        f = {
            "plus": self.model.addVars(sets["employees"]["all"], vtype=GRB.CONTINUOUS, name="f_plus"),
            "minus": self.model.addVars(sets["employees"]["all"], vtype=GRB.CONTINUOUS, name="f_minus"),
        }

        return f

    def add_g(self):

        g = {
            "plus": self.model.addVar(vtype=GRB.CONTINUOUS, name="g_plus"),
            "minus": self.model.addVar(vtype=GRB.CONTINUOUS, name="g_minus"),
        }

        return g
