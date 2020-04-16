from gurobipy import *

from xml_loader import shift_generation

from model.shift_design_constraints import ShiftDesignConstraints
from model.shift_design_objective import ShiftDesignObjective
from model.shift_design_variables import ShiftDesignVariables
from utils.const import *
from utils.weights import *


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
        self.low_dur_shifts = data["shifts"]["low_duration_shifts"]
        self.long_dur_shifts = data["shifts"]["long_duration_shifts"]
        self.desired_shift_dur_low = min(DESIRED_SHIFT_DURATION)
        self.desired_shift_dur_long = max(DESIRED_SHIFT_DURATION)

        self.var = ShiftDesignVariables(
            model=self.model,
            shifts=self.shifts,
            low_dur_shifts=self.low_dur_shifts,
            long_dur_shifts=self.long_dur_shifts,
            time_periods=self.time_periods
        )

        self.constraints = ShiftDesignConstraints(
            model=self.model,
            var=self.var,
            competencies=self.competencies,
            demand=self.demand,
            time_periods=self.time_periods,
            shifts=self.shifts,
            shifts_overlapping_t=self.shifts_overlapping_t,
            low_dur_shifts=self.low_dur_shifts,
            long_dur_shifts=self.long_dur_shifts,
            desired_shift_dur_low=self.desired_shift_dur_low,
            desired_shift_dur_long=self.desired_shift_dur_long
        )

        self.objective = ShiftDesignObjective(
            model=self.model,
            var=self.var,
            weights=self.weights,
            shifts=self.shifts,
            time_periods=self.time_periods,
            low_dur_shifts=self.low_dur_shifts,
            long_dur_shifts=self.long_dur_shifts
        )

    def run_model(self):
        self.model.optimize()
