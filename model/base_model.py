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
        self.time = data["time"]
        self.time_step = data["time"]["step"]
        self.time_periods = data["time"]["periods"]
        self.days = data["time"]["days"]

        self.limit_on_consecutive_days = data["limit_on_consecutive_days"]

        #Heuristic
        self.saturdays = data["time"]["saturdays"]
        self.sundays = data["time"]["sundays"]
        self.employees = data["staff"]["employees"]
        self.t_covered_by_shift = data["heuristic"]["t_covered_by_shift"]
        self.time_periods_in_day = data["time"]["periods"][2]
        self.shift_lookup = data["heuristic"]["shift_lookup"]
        self.shifts_at_day = data["shifts"]["shifts_per_day"]
        self.weeks = data["time"]["weeks"]
        self.contracted_hours = data["staff"]["employee_contracted_hours"]
        self.time_periods = data["time"]["periods"][0]
        self.off_shifts = data["off_shifts"]["off_shifts"]
        self.off_shift_in_week = data["off_shifts"]["off_shifts_per_week"]
        self.shifts_covered_by_off_shift = data["shifts"]["shifts_covered_by_off_shifts"]
        self.shifts_overlapping_t = data["shifts"]["shifts_overlapping_t"]
        self.employee_with_competencies = data["staff"]["employees_with_competencies"]


    def create_model(self):
        return Model(name=self.name)

    def run_model(self):
        self.model.optimize()
