from model.base_constraints import BaseConstraints
from model.base_model import BaseModel
from model.base_variables import BaseVariables
from model.feasibility_objective import FeasibilityObjective


class FeasibilityModel(BaseModel):
    def __init__(self, name):
        super(FeasibilityModel, self).__init__(name)

        self.var = BaseVariables(
            self.model,
            self.competencies,
            self.staff,
            self.shifts_set,
            self.off_shifts_set,
            self.time["periods"],
            self.days,
            self.saturdays,
            self.sundays
        )

        self.constraints = BaseConstraints(
            self.model,
            self.var,
            self.staff,
            self.demand,
            self.competencies,
            self.time,
            self.shifts_set,
            self.off_shifts_set,
        )

        self.objective = FeasibilityObjective(
            self.model, self.var.y, self.competencies, self.staff, self.time
        )

        #For heuristic
        self.x, self.y, self.w = [None, None, None]
