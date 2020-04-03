from heuristic.criterions.abstract_criterion import AbstractCriterion


class GreedyCriterion(AbstractCriterion):
    """ Accepts any candidate with an equal or better solution compared to current solution """

    def accept(self, candidate, current):
        # todo: is this correct according to the algorithm? -Even, 29. March
        return candidate.get_objective_value() >= current.get_objective_value()
