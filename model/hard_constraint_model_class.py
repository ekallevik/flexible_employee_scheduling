from gurobipy import *
from preprocessing.shift_generation import *

#MODEL



class Optimization_model():
    def __init__(self, problem_name):
        self.model = Model("Employee_scheduling")



        data = load_data(problem_name)

        #Employee sets
        self.employees = data["staff"]["employees"]
        self.employee_with_competencies = data["staff"]["employees_with_competencies"]
        self.employee_weekly_rest = data["staff"]["employee_with_weekly_rest"]
        self.employee_daily_rest = data["staff"]["employee_daily_rest"]
        self.contracted_hours = data["staff"]["employee_contracted_hours"]
        self.employee_with_competency_combination = data["staff"]["employee_with_competency_combination"]
        self.competencies = data["competencies"]

        #Time sets
        self.time_step = data["time"]["step"]
        self.time_periods = data["time"]["periods"][0]
        self.time_periods_in_week = data["time"]["periods"][1]
        self.time_periods_in_day = data["time"]["periods"][2]
        self.combined_time_periods = data["time"]["combined_time_periods"][0]
        self.combined_time_periods_in_week = data["time"]["combined_time_periods"][1]
        self.combined_time_periods_in_day = data["time"]["combined_time_periods"][2]

        #Week/days set
        self.days = data["time"]["days"]
        self.weeks = data["time"]["weeks"]
        self.saturdays = data["time"]["saturdays"]
        self.sundays = data["time"]["sundays"]


        self.demand = data["demand"]

        
        #Shift sets
        self.shifts = data["shifts"]["shifts"]
        self.shifts_at_day = data["shifts"]["shifts_per_day"]
        self.shifts_at_week = data["shifts"]["shifts_per_week"]
        self.shifts_overlapping_t = data["shifts"]["shifts_overlapping_t"]
        self.shifts_covered_by_off_shift = data["shifts"]["shifts_covered_by_off_shift"]

        #Off shifts set
        self.t_in_off_shifts = data["off_shifts"]["t_in_off_shifts"]
        self.off_shifts = data["off_shifts"]["off_shifts"]
        self.off_shift_in_week = data["off_shifts"]["off_shifts_per_week"]

        #Daily rest sets:
        self.invalid_shifts = data["shifts"]["invalid_shifts"]
        self.shift_combinations_violating_daily_rest = data["shifts"]["shift_combinations_violating_daily_rest"]
        self.shift_sequences_violating_daily_rest = data["shifts"]["shift_sequences_violating_daily_rest"]

        
        self.L_C_D = data["limit_on_consecutive_days"]

        #Heuristic sets
        self.t_covered_by_shift = data["heuristic"]["t_covered_by_shift"]
        self.shift_lookup = data["heuristic"]


#Variables
    def add_variables(self):

        y = {(c,e,t): 0 for c in self.competencies for e in self.employees for t in self.time_periods[c]}
        #self.delta = {}
        self.ro = {}
        self.q_iso = {}
        self.f = {}
        self.g = {}
        self.y = self.model.addVars(y, vtype=GRB.BINARY, name='y')
        self.x = self.model.addVars(self.employees, self.shifts, vtype=GRB.BINARY, name='x')
        #self.mu = self.model.addVars(self.competencies, self.time_periods, vtype=GRB.INTEGER, name='mu')
        #self.delta["plus"] = self.model.addVars(self.competencies, self.time_periods, vtype=GRB.INTEGER, name='delta_plus')
        #self.delta["minus"] = self.model.addVars(self.competencies, self.time_periods, vtype=GRB.INTEGER, name='delta_minus')
        self.gamma = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='gamma')
        self.w = self.model.addVars(self.employees, self.off_shifts, vtype=GRB.BINARY, name='w')
        self.lam = self.model.addVars(self.employees,vtype=GRB.CONTINUOUS, name='lambda')
        self.ro["sat"] = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='ro_sat')
        self.ro["sun"] = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='ro_sun')
        self.q_iso["off"] = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='q_iso_off')
        self.q_iso["work"] = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='q_iso_work')
        self.q_con = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='q_con')
        self.f["plus"] = self.model.addVars(self.employees, vtype=GRB.CONTINUOUS, name='f_plus')
        self.f["minus"] = self.model.addVars(self.employees, vtype=GRB.CONTINUOUS, name='f_minus')
        self.g["plus"] = self.model.addVar(vtype=GRB.CONTINUOUS, name='g_plus')
        self.g["minus"] = self.model.addVar(vtype=GRB.CONTINUOUS, name='g_minus')



    def add_constraints(self):
        self.model.addConstrs((
            quicksum(self.y[c,e,t] 
            for e in self.employee_with_competencies[c]) 
            >= self.demand["min"][c,t]  
            for c in self.competencies 
            for t in self.time_periods[c]),
        name='minimum_demand_coverage')

        self.model.addConstrs((
            quicksum(self.y[c,e,t] 
            for e in self.employee_with_competencies[c])
            <= self.demand["max"][c,t]
            for c in self.competencies 
            for t in self.time_periods[c]),
        name='less_than_max_demand')


        self.model.addConstrs((
            quicksum(self.x[e,t,v] 
            for t,v in self.shifts_at_day[i]) 
            <= 1 
            for e in self.employees 
            for i in self.days), 
            name="cover_maximum_one_shift")

        self.model.addConstrs((
            quicksum(self.x[e,t_marked,v] 
            for t_marked,v in self.shifts_overlapping_t[t]) 
            == quicksum(self.y[c,e,t] 
                for c in self.competencies 
                if (c,e,t) in self.y)
            for e in self.employees
            for t in self.combined_time_periods
        ),name="mapping_shift_to_demand")

        self.model.addConstrs((
            quicksum(self.y[c,e,t] 
            for c in self.competencies if (c,e,t) in self.y) 
            <= 1 
            for e in self.employees 
            for t in self.combined_time_periods
        ), name="only_cover_one_demand_at_a_time")


        self.model.addConstrs((
            quicksum(self.w[e,t,v] 
            for t,v in self.off_shift_in_week[j]) 
            == 1 
            for e in self.employees 
            for j in self.weeks
        ), name="one_weekly_off_shift_per_week")

        # self.model.addConstrs((
        #     len(self.shifts_covered_by_off_shift[t,v]) * self.w[e,t,v] <= 
        #     quicksum(
        #         quicksum(
        #             (1-self.x[e,t_marked,v_marked]) for c in self.competencies
        #         ) for t_marked,v_marked in self.shifts_covered_by_off_shift[t,v]
        #     ) for e in self.employees for t,v in self.off_shifts
        # ), name="no_work_during_off_shift")

        self.model.addConstrs(
            (
                quicksum(len(self.t_in_off_shifts[t, v, c]) for c in self.competencies if self.t_in_off_shifts.get((t, v, c))) * self.w[e, t, v]
                <= quicksum(1 - self.y[c, e, t_mark] 
                    for c in self.competencies
                    if self.t_in_off_shifts.get((t,v,c))
                    for t_mark in self.t_in_off_shifts[t, v, c]
                    if self.y.get((c,e,t_mark))
                )
                for e in self.employees
                for t, v in self.off_shifts
            ),
            name="no_work_during_off_shift_original",
        )


        self.model.addConstrs((
            quicksum(
                self.time_step * self.y[c,e,t] 
                for c in self.competencies
                for t in self.time_periods[c]
                if self.y.get((c,e,t)))
                <= len(self.weeks)*self.contracted_hours[e] 
                for e in self.employees
        ), name="contracted_hours")

        # self.model.addConstrs((
        #     quicksum(
        #         quicksum(
        #             self.time_step*self.y[c,e,t] for t in self.time_periods
        #         ) for c in self.competencies
        #     ) + self.lam[e] == len(self.weeks)*self.contracted_hours[e] for e in self.employees
        # ), name="contracted_hours")

    def set_objective(self):
        self.model.setObjective(
        quicksum(
                self.y[c,e,t] 
                for e in self.employees
                for c in self.competencies
                for t in self.time_periods[c]
                if(self.y.get((c,e,t)))
        ), GRB.MINIMIZE
    )

    def optimize(self):
        self.model.optimize()
        self.model.write("solution.sol")
        print("#############RESTRICTIONS ADDED#############")


if __name__ == "__main__":
    model = Optimization_model("rproblem3")
    model.add_variables()
    print("#############VARIABLES ADDED#############")
    model.add_constraints()
    print("#############RESTRICTIONS ADDED#############")
    model.set_objective()
    print("#############OBJECTIVE SET#############")
    model.optimize()

