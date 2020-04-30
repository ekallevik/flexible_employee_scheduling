from model.base_model import BaseModel
from model.optimality_constraints import OptimalityConstraints
from model.optimality_objective import OptimalityObjective
from model.optimality_variables import OptimalityVariables



class OptimalityModel(BaseModel):
    def __init__(self, name, problem, data):
        super(OptimalityModel, self).__init__(name, problem, data)

        self.var = OptimalityVariables(
            model=self.model,
            competencies=self.competencies,
            staff=self.staff,
            time_set=self.time_set,
            shifts_set=self.shifts_set,
            off_shifts_set=self.off_shifts_set,
        )

        self.constraints = OptimalityConstraints(
            model=self.model,
            var=self.var,
            staff=self.staff,
            demand=self.demand,
            competencies=self.competencies,
            time_set=self.time_set,
            shifts_set=self.shifts_set,
            off_shifts_set=self.off_shifts_set,
            limit_on_consecutive_days=self.limit_on_consecutive_days,
        )

        self.objective = OptimalityObjective(
            model=self.model,
            var=self.var,
            weights=self.weights,
            competencies=self.competencies,
            preferences=self.preferences,
            staff=self.staff,
            time_set=self.time_set,
            off_shifts_set=self.off_shifts_set,
        )
