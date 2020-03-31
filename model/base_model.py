from abc import ABC, abstractmethod

from gurobipy import *

from xml_loader import shift_generation


class BaseModel:
    """
    This abstract class will take care of all common code that is to be shared across all model variants.
    """

    def __init__(self, name, problem="rproblem2", mip_focus='default', solution_limit='default'):

        self.name = name
        self.model = self.create_model()
        self.mip_focus = mip_focus
        self.solution_limit = solution_limit

        data = shift_generation.load_data(problem)

        self.competencies = data["competencies"]
        self.demand = data["demand"]
        self.staff = data["staff"]
        self.time_set = data["time"]
        self.shift_set = data["shifts"]
        self.off_shift_set = data["off_shifts"]
        self.limit_on_consecutive_days = data["limit_on_consecutive_days"]

    def create_model(self):
        return Model(name=self.name)

    def run_model(self):
        self.model.setParam("MIPFocus", self.mip_focus)
        self.model.setParam("SolutionLimit", self.solution_limit)
        self.model.optimize()
