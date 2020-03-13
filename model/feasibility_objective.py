from gurobipy.gurobipy import GRB, quicksum


class FeasibilityObjective:

    def __init__(self, model, sets, y):

        self.model = model

        self.add_objective(sets, y)

    def add_objective(self, sets, y):

        self.model.setObjective(
            quicksum(
                quicksum(
                    quicksum(y[c, e, t] for e in sets["employees"]["all"]) for c in sets["competencies"]
                )
                for t in sets["time"]["periods"]
            ),
            GRB.MINIMIZE,
        )
