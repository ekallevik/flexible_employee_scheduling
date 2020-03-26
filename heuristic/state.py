class State:
    def __init__(self, x, y, w):

        self.x = x
        self.y = y
        self.w = w

    def get_objective_value(self):
        raise NotImplementedError
