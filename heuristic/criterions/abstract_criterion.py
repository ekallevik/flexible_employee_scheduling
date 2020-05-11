class AbstractCriterion:
    """ Abstract-class to make sure that every criterion implements the necessary methods"""

    def __str__(self):
        raise NotImplementedError

    def accept(self, candidate, current, random_state):
        raise NotImplementedError
