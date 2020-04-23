from gurobipy import *

from utils.weights import get_shift_design_weights
from preprocessing import shift_generation

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

        self.shift_sets = data["shifts"]

        self.var = ShiftDesignVariables(
            model=self.model,
            shift_sets=self.shift_sets,
            time_periods=self.time_periods,
        )

        self.constraints = ShiftDesignConstraints(
            model=self.model,
            var=self.var,
            competencies=self.competencies,
            demand=self.demand,
            time_periods=self.time_periods,
            shift_sets=self.shift_sets,
        )

        self.objective = ShiftDesignObjective(
            model=self.model,
            var=self.var,
            weights=self.weights,
            shift_sets=self.shift_sets,
            time_periods=self.time_periods,
        )

    def run_model(self):
        self.model.optimize()

    def get_used_shifts(self):

        y = self.convert()

        for key, value in y.items():
            print(f"Key: {key}, value: {value}")

        return [shift for shift, used in y.items() if used == 1]

    def convert(self):
        """ Converts a tupledict of Gurobi variables to a tupledict of ints """

        converted_dict = tupledict()

        var = self.var.y

        for key in var.keys():
            # Make sure that values are always positive
            converted_dict[key] = abs(var[key].x)

        return converted_dict
