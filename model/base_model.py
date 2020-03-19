from abc import ABC, abstractmethod

from gurobipy import *

from xml_loader import shift_generation


class BaseModel:
    """
    This abstract class will take care of all common code that is to be shared across all model variants.
    """

    def __init__(self, name, problem="rproblem2"):
        self.name = name
        self.model = self.create_model()

        data = shift_generation.load_data(problem)

        self.competencies = data["competencies"]
        self.demand = data["demand"]
        self.staff = data["staff"]
        self.shifts_set = data["shifts"]
        self.off_shifts_set = data["off_shifts"]
        self.time_set = data["time"]

        # todo: want to remove
        self.time_step = data["time"]["step"]
        self.time_periods = data["time"]["periods"]
        self.days = data["time"]["days"]

        self.limit_on_consecutive_days = data["limit_on_consecutive_days"]

    def create_model(self):
        return Model(name=self.name)

    def run_model(self):
        self.model.optimize()
