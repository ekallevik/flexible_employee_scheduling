import numpy as np

from heuristic.criterions.abstract_criterion import AbstractCriterion


class SimulatedAnnealingCriterion(AbstractCriterion):
    def __init__(self, start_temperature, end_temperature, step, method="linear"):

        self.start_temperature = start_temperature
        self.current_temperature = start_temperature
        self.end_temperature = end_temperature

        self.step = step

        self.method = method

        self.validate()

    def __str__(self):
        return f"SimulatedAnnealingCriterion [t0={self.start_temperature}, " \
               f"t1={self.end_temperature}, step={self.step}, method={self.method}]"

    def accept(self, candidate, current, random_state):

        probability = np.exp(
            (current.get_objective_value() - candidate.get_objective_value())
            / self.current_temperature
        )

        self.update_temperature()

        return probability >= random_state.random()

    def update_temperature(self):
        """
        Updates the current temperature linearly or exponentially.

        Note: end_temperature is the minimum possible temperature.
        """

        if self.method == "linear":
            self.current_temperature = max(
                self.current_temperature - self.step, self.end_temperature
            )
        else:
            self.current_temperature = max(
                self.current_temperature * self.step, self.end_temperature
            )

    def validate(self):

        breakpoint()

        if self.method not in ["linear", "exponential"]:
            raise ValueError(f"Method: {self.method} is not a valid choice")

        if self.start_temperature <= 0 or self.end_temperature <= 0:
            raise ValueError("The temperature must be strictly positive")

        if self.start_temperature < self.end_temperature:
            raise ValueError("The start temperature must be greater than the end temperature")

        if self.step <= 0:
            raise ValueError("The step must be strictly positive")

        if self.step > 1 and self.method == "exponential":
            raise ValueError("The step must be less than 1 for exponential simulated annealing")
