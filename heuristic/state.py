class State:
    def __init__(self, var, sets):

        self.x = var["x"]
        self.y = var["y"]
        self.w = var["w"]

    def get_objective_value(self):
        # todo: will be implemented after Håkon's PR is approved. See https://trello.com/c/baWqgH1d.
        raise NotImplementedError

    def get_working_days(self, employee):
        raise NotImplementedError

    def is_working_day(self, employee, day):
        raise NotImplementedError

