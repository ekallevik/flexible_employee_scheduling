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

        self.var = OptimalityVariables(self.model, self.sets)
        self.constraints = OptimalityConstraints(self.model, self.sets, self.var)

        self.objective = OptimalityObjective(self.model, self.sets, self.var, self.weights)
