from copy import copy, deepcopy

class State:
    def __init__(self, decision_vars, soft_vars, hard_vars, objective_function_value, f):

        #Hard decision variables
        self.x = decision_vars["x"]
        self.y = decision_vars["y"]
        self.w = decision_vars["w"]

        #Soft Variables
        self.soft_vars = soft_vars

        # #Hard Penalty Variables
        self.hard_vars = hard_vars

        self.objective_function_value = objective_function_value
        self.f = f


    def get_objective_value(self):
        return self.objective_function_value


    def copy(self):
        return State({"x": copy(self.x), "y": copy(self.y), "w": copy(self.w)}, deepcopy(self.soft_vars), deepcopy(self.hard_vars), copy(self.objective_function_value), copy(self.f))
