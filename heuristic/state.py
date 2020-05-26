from copy import copy
from collections import defaultdict

from loguru import logger

from heuristic.delta_calculations import hard_constraint_penalties


class State:
    def __init__(self, decision_vars, soft_vars, hard_vars, objective_function_value, f,
                 hard_penalty=1):

        #Hard decision variables
        self.x = decision_vars["x"]
        self.y = decision_vars["y"]
        self.w = decision_vars["w"]

        #Soft Variables
        self.soft_vars = soft_vars

        # Hard Penalty Variables
        self.hard_vars = hard_vars
        self.hard_penalty = hard_penalty

        self.objective_function_value = objective_function_value
        self.f = f

    def get_objective_value(self):
        return self.objective_function_value

    def is_feasible(self):
        """ Returns True if all hard_vars is 0, otherwise will return False """

        return (
                not any(self.hard_vars["below_minimum_demand"].values())
                and not any(self.hard_vars["delta_positive_contracted_hours"].values())
                and not any(self.hard_vars["above_maximum_demand"].values())
                and not any(self.hard_vars["weekly_off_shift_error"].values())
                and not any(self.hard_vars["more_than_one_shift_per_day"].values())
                and not any(self.hard_vars["cover_multiple_demand_periods"].values())
                and not any(self.hard_vars["mapping_shift_to_demand"].values())
                and not any(self.hard_vars["daily_rest_error"].values())
                )

    def copy(self):

        return State(
            {"x": self.x.copy(), "y": self.y.copy(), "w": self.w.copy()},
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
                "delta_positive_contracted_hours": self.hard_vars["delta_positive_contracted_hours"].copy(),
                "daily_rest_error": self.hard_vars["daily_rest_error"].copy()
            },
            copy(self.objective_function_value), copy(self.f))

    def get_violations(self, weeks, time_periods_in_week, competencies, employees):
        """ Extracts all violations of hard constraints per week"""

        below_demand = {
            j: {(c, t):
                self.hard_vars["below_minimum_demand"][c, t]
                for c in competencies
                for t in time_periods_in_week[c, j]
                if self.hard_vars["below_minimum_demand"].get((c, t))
                }
            for j in weeks
        }

        above_demand = {
            j: {(c, t):
                self.hard_vars["above_maximum_demand"][c, t]
                for c in competencies
                for t in time_periods_in_week[c, j]
                if self.hard_vars["above_maximum_demand"].get((c, t))
                }
            for j in weeks
        }

        contracted_hours = {
            j: {e:
                self.soft_vars["deviation_contracted_hours"][e, j]
                for e in employees
                if self.hard_vars["deviation_contracted_hours"].get(e, j)
                }
            for j in weeks
        }

        violations = {
            "above_demand": above_demand,
            "below_demand": below_demand,
            "contracted_hours": contracted_hours
        }

        return violations

    def get_violations_per_week(self, weeks, time_periods_in_week, competencies,
                                            employees):
        """ Sums violations of hard constraints per week"""

        below_demand = [sum(self.hard_vars["below_minimum_demand"].get((c, t), 0)
                            for c in competencies
                            for t in time_periods_in_week[c, week])
                        for week in weeks]

        above_demand = [sum(self.hard_vars["above_maximum_demand"].get((c, t), 0)
                            for c in competencies
                            for t in time_periods_in_week[c, week])
                        for week in weeks]

        contracted_hours = [-sum(self.soft_vars["deviation_contracted_hours"].get((e, j), 0)
                                 for e in employees)
                            for j in weeks]

        violations = {
            "above_demand": above_demand,
            "below_demand": below_demand,
            "contracted_hours": contracted_hours
        }

        return violations

    def write(self, filename):

        summasjon = defaultdict(float)
        f = open(f"{filename}.sol", "w+")
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
        logger.warning(f"Saved ALNS-solution to {filename}.sol")

