from copy import copy

class State:
    def __init__(self, hard_vars, soft_vars):

        #Hard decision variables
        self.x = hard_vars["x"]
        self.y = hard_vars["y"]
        self.w = hard_vars["w"]

        #Soft Variables
        self.soft_vars = soft_vars

        # self.negative_deviation_from_demand
        # self.partial_weekends
        # self.consecutive_days
        # self.isolated_off_days
        # self.isolated_working_days
        # self.contracted_hours

        # #Hard Penalty Variables
        # self.cover_min_demand
        # self.cover_max_demand
        # self.one_demand_per_time
        # self.one_shift_per_day
        # self.one_weekly_off
        # self.work_during_off
        # self.shift_demand_map
        # self.break_contracted_hours



    def get_objective_value(self):
        # todo: will be implemented after Håkon's PR is approved. See https://trello.com/c/baWqgH1d.
        raise NotImplementedError

    def copy(self):
        return State({"x": copy(self.x), "y": copy(self.y), "w": copy(self.w)}, self.soft_vars)