from model.base_constraints import BaseConstraints
from model.base_model import BaseModel
from model.base_variables import BaseVariables
from model.feasibility_objective import FeasibilityObjective


class FeasibilityModel(BaseModel):

    def __init__(self, name):
        super(FeasibilityModel, self).__init__(name)

        self.var = BaseVariables(self.model, self.sets)
        self.constraints = BaseConstraints(self.model, self.sets, self.var)

        self.objective = FeasibilityObjective(self.model, self.sets, self.var.y)
