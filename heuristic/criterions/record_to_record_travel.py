from loguru import logger

from heuristic.criterions.abstract_criterion import AbstractCriterion


class RecordToRecordTravel(AbstractCriterion):
    def __init__(self, start_threshold, end_threshold, step, method="linear"):

        self.start_threshold = start_threshold
        self.current_threshold = start_threshold
        self.end_threshold = end_threshold

        self.step = step

        self.method = method

        self.validate()

    def __str__(self):
        return f"RecordToRecordTravel [t0={self.start_threshold}, " \
               f"t1={self.end_threshold}, step={self.step}, method={self.method}]"

    def accept(self, candidate, current, best, random_state):

        is_accepted = (best.get_objective_value() - candidate.get_objective_value()) <= \
                      self.current_threshold

        self.update_threshold()
        logger.info(f"Accept candidate: {is_accepted}. t={self.current_threshold})")

        return is_accepted

    def update_threshold(self):
        """
        Updates the current temperature linearly or exponentially.

        Note: end_temperature is the minimum possible temperature.
        """

        if self.method == "linear":
            self.current_threshold = max(
                self.current_threshold - self.step, self.end_threshold
            )
        else:
            self.current_threshold = max(
                self.current_threshold * self.step, self.end_threshold
            )

    def validate(self):

        if self.method not in ["linear", "exponential"]:
            raise ValueError(f"Method: {self.method} is not a valid choice")

        if self.start_threshold <= 0 or self.end_threshold <= 0:
            raise ValueError("Thresholds must be strictly positive")

        if self.start_threshold < self.end_threshold:
            raise ValueError("The start threshold must be greater than the end threshold")

        if self.step <= 0:
            raise ValueError("The step must be strictly positive")

        if self.step > 1 and self.method == "exponential":
            raise ValueError("The step must be less than 1 for exponential simulated annealing")
