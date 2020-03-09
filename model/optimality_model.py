from model.model_classes import AbstractModel


class OptimalityModel(AbstractModel):

    def __init__(self):

        super().__init__()

    def add_variables(self):

        feas_var.add_feasibility_variables()
        optim_var.add_optimality_variables()
