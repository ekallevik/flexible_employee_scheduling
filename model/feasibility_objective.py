from gurobipy.gurobipy import GRB, quicksum


class FeasibilityObjective:
    def __init__(self, model, y, competencies, staff, time_set):

        self.model = model

        self.competencies = competencies
        self.employees = staff["employees"]
        self.time_periods = time_set["periods"][0]

        self.add_objective(y)

    def add_objective(self, y):

        self.model.setObjective(
            quicksum(
                quicksum(quicksum(y[c, e, t] for e in self.employees) for c in self.competencies)
                for t in self.time_periods
            ),
            GRB.MINIMIZE,
        )
