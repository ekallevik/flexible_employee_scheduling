from copy import copy
from collections import defaultdict

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
        return State({"x": self.x.copy(), "y": self.y.copy(), "w": self.w.copy()},

        {
        "deviation_from_ideal_demand": self.soft_vars["deviation_from_ideal_demand"].copy(),
        "partial_weekends": self.soft_vars["partial_weekends"].copy(),
        "consecutive_days": self.soft_vars["consecutive_days"].copy(),
        "isolated_off_days": self.soft_vars["isolated_off_days"].copy(),
        "isolated_working_days": self.soft_vars["isolated_working_days"].copy(),
        "deviation_contracted_hours": self.soft_vars["deviation_contracted_hours"].copy()
        },
        {
        "below_minimum_demand": self.hard_vars["below_minimum_demand"].copy(),
        "above_maximum_demand": self.hard_vars["above_maximum_demand"].copy(),
        "more_than_one_shift_per_day": self.hard_vars["more_than_one_shift_per_day"].copy(),
        "cover_multiple_demand_periods": self.hard_vars["cover_multiple_demand_periods"].copy(),
        "weekly_off_shift_error": self.hard_vars["weekly_off_shift_error"].copy(),
        "mapping_shift_to_demand": self.hard_vars["mapping_shift_to_demand"].copy(),
        "delta_positive_contracted_hours": self.hard_vars["delta_positive_contracted_hours"].copy()
        },
        copy(self.objective_function_value), copy(self.f))


    def write(self, filename):
        summasjon = defaultdict(float)
        f = open(filename + ".sol", "w+")
        f.write(f"# Objective value = {self.objective_function_value}\n")

        for c,e,t in self.y:
            f.write(f"y[{c},{e},{t}] {int(self.y[c,e,t])}\n")

        for e, t, v in self.x:
            f.write(f"x[{e},{t},{v}] {int(self.x[e,t,v])}\n")

        for e,j in self.w:
            f.write(f"w[{e},{self.w[e,j][0]},{self.w[e,j][1]}] 1\n")

        for key in self.soft_vars.keys():
            if(key == "deviation_contracted_hours"):
                for key2 in self.soft_vars[key]:
                    summasjon[key2[0]] += float(self.soft_vars[key][key2])
                for e in summasjon:
                    f.write(f"deviation_contracted_hours[{e}] {summasjon[e]}\n")
            else:
                for key2 in self.soft_vars[key]:
                    f.write("%s[%s] %s\n" % (key, ''.join(str(key2)), str(int(self.soft_vars[key][key2]))))

        for key in self.f:
            f.write(f"f[{key}] {self.f[key]}\n")

        f.write("\nHard Variables Penalising Objective Function:\n")
        for key in self.hard_vars.keys():
            for key2 in self.hard_vars[key]:
                f.write("%s[%s] %s\n" % (key, ''.join(str(key2)), str(int(self.hard_vars[key][key2]))))

        f.close()
