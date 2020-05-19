from heuristic.criterions.abstract_criterion import AbstractCriterion


class GreedyCriterion(AbstractCriterion):
    """ Accepts any candidate with an equal or better solution compared to current solution """

    def __str__(self):
        return "GreedyCriterion"

    def accept(self, candidate, current, random_state):
        return candidate.get_objective_value() > current.get_objective_value()
