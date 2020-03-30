from model.base_constraints import BaseConstraints
from model.base_model import BaseModel
from model.base_variables import BaseVariables
from model.feasibility_objective import FeasibilityObjective


class FeasibilityModel(BaseModel):
    def __init__(self, name, problem):
        super(FeasibilityModel, self).__init__(name, problem)

        self.var = BaseVariables(
            self.model,
            self.competencies,
            self.staff,
            self.shift_set,
            self.off_shift_set,
            self.time_set["periods"],
            self.days,
            self.saturdays,
            self.sundays
        )

        self.constraints = BaseConstraints(
            model=self.model,
            var=self.var,
            competencies=self.competencies,
            staff=self.staff,
            demand=self.demand,
            time_set=self.time_set,
            shift_set=self.shift_set,
            off_shift_set=self.off_shift_set,
        )

        self.objective = FeasibilityObjective(
            model=self.model,
            y=self.var.y,
            competencies=self.competencies,
            staff=self.staff,
            time_set=self.time_set,
        )

        #For heuristic
        self.x, self.y, self.w = [None, None, None]
