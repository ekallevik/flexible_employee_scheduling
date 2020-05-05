
from gurobipy import *
from utils.weights import get_weights


class BaseModel:
    """
    This abstract class will take care of all common code that is to be shared across all model variants.
    """

    def __init__(self, model, data):

        self.model = model

        self.competencies = data["competencies"]
        self.demand = data["demand"]
        self.staff = data["staff"]
        self.time_set = data["time"]
        self.shifts_set = data["shifts"]
        self.off_shifts_set = data["off_shifts"]
        self.limit_on_consecutive_days = data["limit_on_consecutive_days"]
        self.preferences = data["preferences"]

        self.weights = get_weights(self.time_set, self.staff)

        self.var = None

    def run_model(self):
        self.model.optimize()

    def get_variables(self):
        """ This method is intended to be used in all subclasses of BaseModel"""
        return self.var

    def get_objective_value(self):
        """ Returns the object value of the found solution """
        return self.model.getObjective().getValue()
