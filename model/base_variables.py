from gurobipy import *


class BaseVariables:
    def __init__(self, model, sets):
        self.model = model

        self.x = self.add_x(sets)
        self.y = self.add_y(sets)
        self.w = self.add_w(sets)
        self.mu = self.add_mu(sets)
        self.delta = self.add_delta(sets)
        self.gamma = self.add_gamma(sets)
        self.lam = self.add_lambda(sets)

    def add_y(self, sets):
        return self.model.addVars(
            sets["competencies"],
            sets["employees"]["all"],
            sets["time"]["periods"],
            vtype=GRB.BINARY,
            name="y",
        )

    def add_x(self, sets):
        return self.model.addVars(
            sets["employees"]["all"], sets["shifts"]["shifts"], vtype=GRB.BINARY, name="x"
        )

    def add_w(self, sets):
        return self.model.addVars(
            sets["employees"]["all"], sets["shifts"]["off_shifts"], vtype=GRB.BINARY, name="w"
        )

    def add_mu(self, sets):
        return self.model.addVars(
            sets["competencies"], sets["time"]["periods"], vtype=GRB.INTEGER, name="mu"
        )

    def add_delta(self, sets):

        delta = {
            "plus": self.model.addVars(
                sets["competencies"], sets["time"]["periods"], vtype=GRB.INTEGER, name="delta_plus"
            ),
            "minus": self.model.addVars(
                sets["competencies"], sets["time"]["periods"], vtype=GRB.INTEGER, name="delta_minus"
            ),
        }

        return delta

    def add_gamma(self, sets):
        return self.model.addVars(
            sets["employees"]["all"], sets["time"]["days"], vtype=GRB.BINARY, name="gamma"
        )

    def add_lambda(self, sets):
        return self.model.addVars(sets["employees"]["all"], vtype=GRB.CONTINUOUS, name="lambda")
