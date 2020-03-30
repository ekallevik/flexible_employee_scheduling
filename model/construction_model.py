from model.base_constraints import BaseConstraints
from model.base_model import BaseModel
from model.base_variables import BaseVariables
from model.construction_objective import ConstructionObjective
from utils import weights


class ConstructionModel(BaseModel):
    def __init__(self, name, problem):
        super(ConstructionModel, self).__init__(name, problem, mip_focus=1)

        self.weights = weights.get_weights()

        self.var = BaseVariables(
            model=self.model,
            competencies=self.competencies,
            staff=self.staff,
            time_set=self.time_set,
            shift_set=self.shift_set,
            off_shift_set=self.off_shift_set,
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

        self.objective = ConstructionObjective(
            model=self.model,
            var=self.var,
            weights=self.weights,
            competencies=self.competencies,
            staff=self.staff,
            time_set=self.time_set,
        )
