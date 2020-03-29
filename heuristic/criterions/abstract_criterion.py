

class AbstractCriterion:
    """ Abstract-class to make sure that every criterion implements the necessary methods"""

    def accept(self, candidate, current):
        raise NotImplementedError
