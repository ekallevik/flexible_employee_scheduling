class State:
    def __init__(self, x, y, w):
        """

        :param x: dict with keys '[e][t][v]'
        :param y: dict with keys '[c][e][t]'
        :param w: dict with keys '[e][t][v]'
        """

        self.x = x
        self.y = y
        self.w = w



    def get_objective_value(self):
        # todo: will be implemented after Håkon's PR is approved. See https://trello.com/c/baWqgH1d.
        raise NotImplementedError

    def is_working_day(self, employee, day):

        
