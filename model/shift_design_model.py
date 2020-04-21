from gurobipy import *

from utils.weights import get_shift_design_weights
from xml_loader import shift_generation

from model.shift_design_constraints import ShiftDesignConstraints
from model.shift_design_objective import ShiftDesignObjective
from model.shift_design_variables import ShiftDesignVariables


class ShiftDesignModel:
    def __init__(self, name, problem="rproblem3"):

        self.name = name
        self.model = Model(name=self.name)

        data = shift_generation.load_data(problem)

        self.weights = get_shift_design_weights()

        self.competencies = data["competencies"]
        self.demand = data["demand"]
        self.time_periods = data["time"]["periods"][0]
        self.shifts = data["shifts"]["shifts"]
        self.shifts_overlapping_t = data["shifts"]["shifts_overlapping_t"]
        self.short_shifts = data["shifts"]["short_shifts"]
        self.long_shifts = data["shifts"]["long_shifts"]

        self.var = ShiftDesignVariables(
            model=self.model,
            shifts=self.shifts,
            short_shifts=self.short_shifts,
            long_shifts=self.long_shifts,
            time_periods=self.time_periods,
        )

        self.constraints = ShiftDesignConstraints(
            model=self.model,
            var=self.var,
            competencies=self.competencies,
            demand=self.demand,
            time_periods=self.time_periods,
            shifts=self.shifts,
            shifts_overlapping_t=self.shifts_overlapping_t,
            short_shifts=self.short_shifts,
            long_shifts=self.long_shifts,
        )

        self.objective = ShiftDesignObjective(
            model=self.model,
            var=self.var,
            weights=self.weights,
            shifts=self.shifts,
            time_periods=self.time_periods,
            short_shifts=self.short_shifts,
            long_shifts=self.long_shifts,
        )

    def run_model(self):
        self.model.optimize()
