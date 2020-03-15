from gurobipy.gurobipy import GRB, quicksum


class FeasibilityObjective:
    def __init__(self, model, y, competencies, staff, time):

        self.model = model

        self.employees = staff["employees"]
        self.competencies = competencies
        self.time_periods = time["periods"]

        self.add_objective(y)

    def add_objective(self, y):

        self.model.setObjective(
            quicksum(
                quicksum(quicksum(y[c, e, t] for e in self.employees) for c in self.competencies)
                for t in self.time_periods
            ),
            GRB.MINIMIZE,
        )
