from abc import ABC, abstractmethod

from gurobipy import *

from model.base_constraints import BaseConstraints
from model.base_variables import BaseVariables
from utils.sets import get_sets
from utils.weights import get_weights


class BaseModel:
    """
    This abstract class will take care of all common code that is to be shared across all model variants.
    """

    def __init__(self, name):
        self.name = name
        self.model = self.create_model()

        self.sets = get_sets()

    def create_model(self):
        return Model(name=self.name)

    def run_model(self):
        self.model.optimize()
