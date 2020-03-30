from model.base_model import BaseModel
from model.optimality_constraints import OptimalityConstraints
from model.optimality_objective import OptimalityObjective
from model.optimality_variables import OptimalityVariables
from utils.weights import get_weights


class OptimalityModel(BaseModel):
    def __init__(self, name, problem):
        super(OptimalityModel, self).__init__(name, problem)

        self.weights = get_weights()

        self.var = OptimalityVariables(
            self.model,
            self.competencies,
            self.staff,
            self.shift_set,
            self.off_shift_set,
            self.time_set["periods"],
            self.days,
            self.saturdays,
            self.sundays,
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
            self.model,
            self.var,
            self.weights,
            self.competencies,
            self.staff,
            self.time_set,
            self.off_shift_set,
            self.saturdays,
        )
