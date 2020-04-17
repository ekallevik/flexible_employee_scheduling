from copy import copy, deepcopy

class State:
    def __init__(self, decision_vars, soft_vars, hard_vars, objective_function_value, f):

        #Hard decision variables
        self.x = decision_vars["x"]
        self.y = decision_vars["y"]
        self.w = decision_vars["w"]

        #Soft Variables
        self.soft_vars = soft_vars

        # self.negative_deviation_from_demand
        # self.partial_weekends
        # self.consecutive_days
        # self.isolated_off_days
        # self.isolated_working_days
        # self.contracted_hours

        # #Hard Penalty Variables
        self.hard_vars = hard_vars

        # self.cover_min_demand
        # self.cover_max_demand
        # self.one_demand_per_time
        # self.one_shift_per_day
        # self.one_weekly_off
        # self.work_during_off
        # self.shift_demand_map
        # self.break_contracted_hours

        self.objective_function_value = objective_function_value
        self.f = f


    def get_objective_value(self):
        return self.objective_function_value

    def copy(self):
        return State({"x": copy(self.x), "y": copy(self.y), "w": copy(self.w)}, deepcopy(self.soft_vars), copy(self.hard_vars), copy(self.objective_function_value), copy(self.f))



    