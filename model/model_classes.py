from abc import ABC

from model import sets, weights


class AbstractModel():


    def __init__(self):

        self.variables = None
        self.model

        self.sets = sets.get_sets()
        self.weights = weights.get_weights()

    def add_variables(self):
        raise NotImplementedError

    def add_constraints(self):
        raise NotImplementedError

    def add_objective(self):
        raise NotImplementedError


class FeasibilityModel(AbstractModel):

    def __init__(self):
        super().__init__()

    def add_variables(self):

        add_feasibility_variables()

    def add_constraints(self):

        add_feasibility_constraints()


    def add_objective(self):

        pass

    Å

