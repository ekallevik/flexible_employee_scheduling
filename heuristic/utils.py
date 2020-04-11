from enum import Enum


class WeightUpdate(Enum):
    # todo: we should add proper values here, so we can use them in weight-updating
    IS_BEST = 1.3
    IS_BETTER = 1.2
    IS_ACCEPTED = 1.1
    IS_REJECTED = 0.9
