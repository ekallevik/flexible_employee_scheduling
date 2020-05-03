from model.base_constraints import BaseConstraints
from model.base_model import BaseModel
from model.base_variables import BaseVariables
from model.construction_objective import ConstructionObjective


class ConstructionModel(BaseModel):
    def __init__(self, model, data):
        super().__init__(model, data)

        self.var = BaseVariables(
            model=self.model,
            competencies=self.competencies,
            staff=self.staff,
            time_set=self.time_set,
            shifts_set=self.shifts_set,
            off_shifts_set=self.off_shifts_set,
        )

        self.constraints = BaseConstraints(
            model=self.model,
            var=self.var,
            competencies=self.competencies,
            staff=self.staff,
            demand=self.demand,
            time_set=self.time_set,
            shifts_set=self.shifts_set,
            off_shifts_set=self.off_shifts_set,
        )

        self.objective = ConstructionObjective(
            model=self.model,
            var=self.var,
            weights=self.weights,
            competencies=self.competencies,
            staff=self.staff,
            time_set=self.time_set,
        )
