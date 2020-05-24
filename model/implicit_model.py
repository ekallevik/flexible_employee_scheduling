
from loguru import logger

from model.implicit_variables import ImplicitVariables
from model.implicit_constraints import ImplicitConstraints
from model.implicit_objective import ImplicitObjective
from utils.weights import get_weights


class ImplicitModel:

    def __init__(self, model, data):

        self.model = model
        self.weights = get_weights(data["time"], data["staff"])

        # Retrieve relevant data from "data"
        self.employees = data["staff"]["employees"]
        self.combined_time_periods = data["time"]["combined_time_periods"][0]
        self.time_periods = data["time"]["periods"][0]
        self.every_time_period = data["time"]["every_time_period"]
        self.competencies = data["competencies"]
        self.days = data["time"]["days"]
        self.preferences = data["preferences"]
        self.shift_durations = data["shift_durations"]

        self.var = ImplicitVariables(
            model=self.model,
            employees=self.employees,
            combined_time_periods=self.combined_time_periods,
            time_periods=self.time_periods,
            every_time_period=self.every_time_period,
            shift_durations=self.shift_durations,
            competencies=self.competencies,
            days=self.days
        )

        self.constraints = ImplicitConstraints(
            model=self.model,
            var=self.var,
            data=data,
        )

        self.objective = ImplicitObjective(
            model=self.model,
            var=self.var,
            weights=self.weights,
            competencies=self.competencies,
            preferences=self.preferences,
            staff=data["staff"],
            time_set=data["time"],
            shift_durations=self.shift_durations
        )

    def run_model(self):
        self.model.optimize()
        logger.error(f"Model is {self.model.status}")

    def get_variables(self):
        """ Return vars used in the model """
        return self.var

    def get_objective_value(self):
        """ Returns the object value of the found solution """
        return self.model.getObjective().getValue()

    def save_solution(self, filename):
        self.model.write(f"solutions/{filename}-ESP.sol")