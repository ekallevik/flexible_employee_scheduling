from gurobipy import *

from model.shift_design_constraints import ShiftDesignConstraints
from model.shift_design_objective import ShiftDesignObjective
from model.shift_design_variables import ShiftDesignVariables
from utils.weights import get_shift_design_weights


class ShiftDesignModel:
    def __init__(self, model, data):

        self.model = model

        self.weights = get_shift_design_weights(data["time"])

        self.competencies = data["competencies"]
        self.demand = data["demand"]
        self.time_periods = data["time"]["periods"][0]
        self.time_periods_combined = data["time"]["combined_time_periods"][0]

        self.shift_sets = data["shifts"]

        self.var = ShiftDesignVariables(
            model=self.model,
            shift_sets=self.shift_sets,
            time_periods=self.time_periods,
            time_periods_combined=self.time_periods_combined,
            competencies=self.competencies
        )

        self.constraints = ShiftDesignConstraints(
            model=self.model,
            var=self.var,
            competencies=self.competencies,
            demand=self.demand,
            time_periods=self.time_periods,
            shift_sets=self.shift_sets,
            time_periods_combined=self.time_periods_combined
        )

        self.objective = ShiftDesignObjective(
            model=self.model,
            var=self.var,
            weights=self.weights,
            shift_sets=self.shift_sets,
            time_periods=self.time_periods,
            competencies=self.competencies
        )

    def run_model(self):
        self.model.optimize()

    def get_used_shifts(self):

        y = self.convert()
        shifts = [shift for shift, used in y.items() if used == 1]

        return tuplelist(shifts)

    def convert(self):
        """ Converts a tupledict of Gurobi variables to a tupledict of ints """

        # todo: move this into separate file for greater re-use

        converted_dict = tupledict()

        var = self.var.y

        for key in var.keys():
            # Make sure that values are always positive
            converted_dict[key] = abs(var[key].x)

        return converted_dict
