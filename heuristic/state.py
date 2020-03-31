from copy import copy

class State:
    def __init__(self, var):

        self.x = var["x"]
        self.y = var["y"]
        self.w = var["w"]

    def get_objective_value(self):
        # todo: will be implemented after Håkon's PR is approved. See https://trello.com/c/baWqgH1d.
        raise NotImplementedError

    def copy(self):
        return State({"x": copy(self.x), "y": copy(self.y), "w": copy(self.w)})