class State:
    def __init__(self, var):

        self.x = var["x"]
        self.y = var["y"]
        self.w = var["w"]

    def get_objective_value(self):
        raise NotImplementedError
