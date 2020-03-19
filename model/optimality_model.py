from model.base_model import BaseModel
from model.optimality_constraints import OptimalityConstraints
from model.optimality_objective import OptimalityObjective
from model.optimality_variables import OptimalityVariables
from utils.weights import get_weights


class OptimalityModel(BaseModel):
    def __init__(self, name):
        super(OptimalityModel, self).__init__(name)

        self.weights = get_weights()

        self.var = OptimalityVariables(
            model=self.model,
            competencies=self.competencies,
            staff=self.staff,
            time_set=self.time_set,
            shift_set=self.shift_set,
            off_shift_set=self.off_shift_set
        )

        self.constraints = OptimalityConstraints(
            model=self.model,
            var=self.var,
            staff=self.staff,
            demand=self.demand,
            competencies=self.competencies,
            time_set=self.time_set,
            shift_set=self.shift_set,
            off_shift_set=self.off_shift_set,
            limit_on_consecutive_days=self.limit_on_consecutive_days,
        )

        self.objective = OptimalityObjective(
            model=self.model,
            var=self.var,
            weights=self.weights,
            competencies=self.competencies,
            staff=self.staff,
            time_set=self.time_set,
            off_shift_set=self.off_shift_set,
        )
