from gurobipy.gurobipy import GRB, quicksum


class ConstructionObjective:
    def __init__(self, model, var, weights, competencies, staff, time_set):

        self.model = model

        self.competencies = competencies
        self.employees = staff["employees"]
        self.time_periods = time_set["periods"][0]

        self.add_objective(weights, var.delta)

    def add_objective(self, weights, delta):

        self.model.setObjective(
            - quicksum(
                quicksum(weights["excess demand deviation factor"] * delta["plus"][c, t] +
                         weights["deficit demand deviation factor"] * delta["minus"][c, t]
                         for t in self.time_periods[c])
                for c in self.competencies
            ),
            GRB.MAXIMIZE,
        )
