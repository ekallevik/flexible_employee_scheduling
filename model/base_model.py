from abc import ABC, abstractmethod

from gurobipy import *
from utils.weights import get_weights

from preprocessing import shift_generation


class BaseModel:
    """
    This abstract class will take care of all common code that is to be shared across all model variants.
    """

    def __init__(self, name, problem, data, mip_focus="default", solution_limit="default"):

        self.name = name
        self.model = self.create_model()
        self.mip_focus = mip_focus
        self.solution_limit = solution_limit

        self.competencies = data["competencies"]
        self.demand = data["demand"]
        self.staff = data["staff"]
        self.time_set = data["time"]
        self.shifts_set = data["shifts"]
        self.off_shifts_set = data["off_shifts"]
        self.limit_on_consecutive_days = data["limit_on_consecutive_days"]
        self.preferences = data["preferences"]
        self.var = None

        self.weights = get_weights(self.time_set, self.staff)

        # Heuristic
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
        self.shifts_covered_by_off_shift = data["shifts"]["shifts_covered_by_off_shift"]
        self.shifts_overlapping_t = data["shifts"]["shifts_overlapping_t"]
        self.employee_with_competencies = data["staff"]["employees_with_competencies"]
        self.days = data["time"]["days"]
        self.time_step = data["time"]["step"]

    def create_model(self):
        return Model(name=self.name)

    def run_model(self):
        self.model.setParam("MIPFocus", self.mip_focus)
        self.model.setParam("SolutionLimit", self.solution_limit)
        self.model.optimize()
        self.model.write("solution.sol")

    def get_variables(self):
        """ This method is intended to be used in all subclasses of BaseModel"""
        return self.var
