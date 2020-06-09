from gurobipy import *


class ImplicitVariables:

    def __init__(self, model, employees, combined_time_periods, time_periods, every_time_period, time_periods_with_no_demand, shift_durations, competencies, days):

        self.model = model

        self.employees = employees
        self.combined_time_periods = combined_time_periods
        self.time_periods = time_periods
        self.every_time_period = every_time_period
        self.time_periods_with_no_demand = time_periods_with_no_demand
        self.shift_durations = shift_durations
        self.competencies = competencies
        self.days = days

        # Adding all variables
        self.x = self.add_x()
        self.y = self.add_y()
        self.w_day = self.add_w_day()
        self.w_week = self.add_w_week()
        self.f = self.add_f()
        self.g = self.add_g()
        self.lam = self.add_lam()
        self.mu = self.add_mu()
        self.delta = self.add_delta()
        self.gamma = self.add_gamma()
        self.q = self.add_q()
        self.rho = self.add_rho()

    def add_x(self):
        x = {(e, t, v): 0
             for e in self.employees
             for t in self.combined_time_periods
             for v in self.shift_durations["work"]
            }
        return self.model.addVars(x, vtype=GRB.BINARY, name="x")

    def add_y(self):
        y = {(c, e, t): 0
             for c in self.competencies
             for e in self.employees
             for t in self.time_periods[c]
             }
        return self.model.addVars(y, vtype=GRB.BINARY, name="y")

    def add_w_day(self):
        w_day = {(e, t, v): 0
                 for e in self.employees
                 for v in self.shift_durations["daily_off"]
                 for t in self.every_time_period
                 }
        return self.model.addVars(w_day, vtype=GRB.BINARY, name="w_day")

    def add_w_week(self):
        w_week = {(e, t, v): 0
                  for e in self.employees
                  for v in self.shift_durations["weekly_off"]
                  for t in self.every_time_period
                  }
        return self.model.addVars(w_week, vtype=GRB.BINARY, name="w_week")

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

    def add_lam(self):
        return self.model.addVars(self.employees, vtype=GRB.CONTINUOUS, name="lambda")

    def add_mu(self):
        mu = {(c, t): 0 for c in self.competencies for t in self.time_periods[c]}
        return self.model.addVars(mu, vtype=GRB.INTEGER, name="mu")

    def add_delta(self):
        plus = {(c, t): 0 for c in self.competencies for t in self.time_periods[c]}
        minus = {(c, t): 0 for c in self.competencies for t in self.time_periods[c]}
        return {
            "plus": self.model.addVars(plus, vtype=GRB.INTEGER, name="delta_plus"),
            "minus": self.model.addVars(minus, vtype=GRB.INTEGER, name="delta_minus"),
        }

    def add_gamma(self):
        return self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name="gamma")

    def add_q(self):
        return {
            "iso_off": self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name="q_iso_off"),
            "iso_work": self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name="q_iso_work"),
            "con": self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name="q_con"),
        }

    def add_rho(self):
        return {
            "sat": self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name="rho_sat"),
            "sun": self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name="rho_sun"),
        }
