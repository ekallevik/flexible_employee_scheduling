from gurobipy import *

from model.base_variables import BaseVariables


class OptimalityVariables(BaseVariables):
    def __init__(
        self, model, competencies, employees, shifts_set, off_shifts_set, time_periods, days, saturdays, sundays
    ):

        super(OptimalityVariables, self).__init__(
            model, competencies, employees, shifts_set, off_shifts_set, time_periods, days, saturdays, sundays


        self.rho = self.add_rho()
        self.q = self.add_q()
        self.gamma = self.add_gamma()
        self.f = self.add_f()
        self.g = self.add_g()

    def add_gamma(self):
        return self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name="gamma")

    def add_rho(self):

        return {
            "sat": self.model.addVars(self.employees, self.saturdays, vtype=GRB.BINARY, name="rho_sat"),
            "sun": self.model.addVars(self.employees, self.sundays, vtype=GRB.BINARY, name="rho_sun"),
        }

    def add_q(self):

        return {
            "iso_off": self.model.addVars(
                self.employees, self.days, vtype=GRB.BINARY, name="q_iso_off"
            ),
            "iso_work": self.model.addVars(
                self.employees, self.days, vtype=GRB.BINARY, name="q_iso_work"
            ),
            "con": self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name="q_con"),
        }

    def add_f(self):

        return {
            "plus": self.model.addVars(self.employees, vtype=GRB.CONTINUOUS, name="f_plus"),
            "minus": self.model.addVars(self.employees, vtype=GRB.CONTINUOUS, name="f_minus"),
        }

    def add_g(self):

        return {
            "plus": self.model.addVar(vtype=GRB.CONTINUOUS, name="g_plus"),
            "minus": self.model.addVar(vtype=GRB.CONTINUOUS, name="g_minus"),
        }
