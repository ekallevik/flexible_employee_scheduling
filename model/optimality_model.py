from model import optimality_objective
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
            self.model,
            self.competencies,
            self.staff,
            self.shifts_set,
            self.off_shifts_set,
            self.time["periods"],
            self.days,
            self.saturdays,
            self.sundays,
        )
        self.constraints = OptimalityConstraints(
            self.model,
            self.var,
            self.staff,
            self.demand,
            self.competencies,
            self.time,
            self.shifts_set,
            self.off_shifts_set,
            self.limit_on_consecutive_days,
        )

        self.objective = OptimalityObjective(
            self.model,
            self.var,
            self.weights,
            self.competencies,
            self.staff,
            self.time,
            self.off_shifts_set,
            self.saturdays,
        )
