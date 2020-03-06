from gurobipy import *
from xml_loader.xml_loader import *

#MODEL



class Optimization_model():
    def __init__(self):
        self.model = Model("Employee_scheduling_haakon")
        self.employees, self.employee_with_competencies, self.employee_weekly_rest, self.employee_daily_rest, self.contracted_hours = get_employee_lists()
        self.competencies = [0]
        self.time_step = get_time_steps()
        self.time_periods, self.time_periods_in_week = get_time_periods()
        self.demand_min, self.demand_ideal, self.demand_max = get_demand_periods()
        self.shifts, self.shifts_at_day = get_shift_lists()
        self.days = get_days()
        self.shifts_covered_by_off_shift = get_shifts_covered_by_off_shifts()
        self.shifts_overlapping_t = get_shifts_overlapping_t()
        self.t_in_off_shifts = get_t_covered_by_off_shifts()
        self.off_shifts, self.off_shift_in_week = get_off_shifts()
        self.weeks = [w for w in range(int(len(self.days)/7))]
        self.saturdays = [5 + (i*7) for i in range(len(self.weeks))]
        self.L_C_D = 5

        self.weights =   {
                "rest": 5,
                "contracted hours": 1,
                "partial weekends": 1,
                "isolated working self.days": 1,
                "isolated off self.days": 1,
                "consecutive self.days": 1,
                "backward rotation": 1,
                "preferences": 1,
                "lowest fairness score" : 1,
                "demand_deviation" : 5
            }


#Variables
    def add_variables(self):
        self.y = self.model.addVars(self.competencies,  self.employees, self.time_periods, vtype=GRB.BINARY, name='y')
        self.x = self.model.addVars(self.employees, self.shifts, vtype=GRB.BINARY, name='x')
        self.mu = self.model.addVars(self.competencies, self.time_periods, vtype=GRB.INTEGER, name='mu')
        self.delta_plus = self.model.addVars(self.competencies, self.time_periods, vtype=GRB.INTEGER, name='delta_plus')
        self.delta_minus = self.model.addVars(self.competencies, self.time_periods, vtype=GRB.INTEGER, name='delta_minus')
        self.gamma = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='gamma')
        self.w = self.model.addVars(self.employees, self.off_shifts, vtype=GRB.BINARY, name='w')
        self.lam = self.model.addVars(self.employees,vtype=GRB.CONTINUOUS, name='lambda')
        self.ro_sat = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='ro_sat')
        self.ro_sun = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='ro_sun')
        self.q_iso_off = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='q_iso_off')
        self.q_iso_work = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='q_iso_work')
        self.q_con = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='q_con')
        self.f_plus = self.model.addVars(self.employees, vtype=GRB.CONTINUOUS, name='f_plus')
        self.f_minus = self.model.addVars(self.employees, vtype=GRB.CONTINUOUS, name='f_minus')
        self.g_plus = self.model.addVar(vtype=GRB.CONTINUOUS, name='g_plus')
        self.g_minus = self.model.addVar(vtype=GRB.CONTINUOUS, name='g_minus')



    def add_constraints(self):
        self.model.addConstrs((quicksum(self.y[c,e,t] for e in self.employee_with_competencies[c]) 
        == self.demand_min[c,t] + self.mu[c,t]  
        for c in self.competencies 
        for t in self.time_periods),
        name='minimum_demand_coverage')

        self.model.addConstrs((self.mu[c,t] 
        <= self.demand_max[c,t] - self.demand_min[c,t]
            for c in self.competencies 
            for t in self.time_periods),
        name='mu_less_than_difference')

        self.model.addConstrs((
            self.mu[c,t] + self.demand_min[c,t] - self.demand_ideal[c,t] 
            == self.delta_plus[c,t] - self.delta_minus[c,t] 
            for t in self.time_periods 
            for c in self.competencies),
        name="deviation_from_ideel_demand")

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
            == quicksum(self.y[c,e,t] for c in self.competencies)
            for e in self.employees
            for t in self.time_periods
        ),name="mapping_shift_to_demand")

        self.model.addConstrs((
            quicksum(self.y[c,e,t] 
            for c in self.competencies) 
            <= 1 
            for e in self.employees 
            for t in self.time_periods
        ), name="only_cover_one_demand_at_a_time")

        self.model.addConstrs((
            quicksum(self.x[e,t,v] 
            for t,v in self.shifts_at_day[i]) 
            == self.gamma[e,i] 
            for e in self.employees 
            for i in self.days
        ), name="if_employee_e_works_day_i")

        self.model.addConstrs((
            quicksum(self.w[e,t,v] 
            for t,v in self.off_shift_in_week[j]) 
            == 1 
            for e in self.employees 
            for j in self.weeks
        ), name="one_weekly_off_shift_per_week")

        self.model.addConstrs((
            len(self.shifts_covered_by_off_shift[t,v]) * self.w[e,t,v] <= 
            quicksum(
                quicksum(
                    (1-self.x[e,t_marked,v_marked]) for c in self.competencies
                ) for t_marked,v_marked in self.shifts_covered_by_off_shift[t,v]
            ) for e in self.employees for t,v in self.off_shifts
        ), name="no_work_during_off_shift")

        self.model.addConstrs((
            quicksum(
                quicksum(
                    self.time_step * self.y[c,e,t] for t in self.time_periods
                ) for c in self.competencies
            ) + self.lam[e] == len(self.weeks)*self.contracted_hours[e] for e in  self.employees
        ), name="contracted_hours")


        self.model.addConstrs((
            quicksum(
                quicksum(
                    self.time_step*self.y[c,e,t] for t in self.time_periods_in_week[j]
                ) for c in self.competencies
            ) >= 0.1*self.contracted_hours[e] for e in  self.employees for j in self.weeks
        ), name="min_weekly_work_hours")

        self.model.addConstrs((
            quicksum(
                quicksum(
                    self.time_step*self.y[c,e,t] for t in self.time_periods_in_week[j]
                ) for c in self.competencies
            ) <= 1.4*self.contracted_hours[e] for e in  self.employees for j in self.weeks
        ), name="maximum_weekly_work_hours")

        #Soft Constraints
        self.model.addConstrs((
            self.gamma[e,i] - self.gamma[e,(i+1)] 
            == self.ro_sat[e,i] - self.ro_sun[e,(i+1)] 
            for e in  self.employees 
            for i in self.saturdays
        ), name="partial_weekends")

        self.model.addConstrs((
            -self.gamma[e,i] + self.gamma[e,(i+1)] - self.gamma[e,(i+2)] 
            <= self.q_iso_work[e,(i+1)] 
            for e in  self.employees 
            for i in range(len(self.days)-2)
        ), name="isolated_working_days")

        self.model.addConstrs((
            self.gamma[e,i] - self.gamma[e,(i+1)] + self.gamma[e,(i+2)] - 1 
            <= self.q_iso_off[e,(i+1)] 
            for e in  self.employees 
            for i in range(len(self.days)-2)
        ), name="isolated_off_days")

        self.model.addConstrs((
            quicksum(
                self.gamma[e,i_marked] 
                for i_marked in range(i, i+self.L_C_D)) - self.L_C_D 
                <= self.q_con[e,i] 
                for e in  self.employees 
                for i in range(len(self.days) - self.L_C_D)
        ), name="consecutive_days")

        
        self.model.addConstrs((
                self.f_plus[e] - self.f_minus[e] ==
                self.weights["rest"] * quicksum(v * self.w[e,t,v] for t,v in self.off_shifts)
                - self.weights["contracted hours"] * self.lam[e]
                - self.weights["partial weekends"] * quicksum(self.ro_sat[e,j] + self.ro_sun[e,j] for j in self.weeks)
                - self.weights["isolated working self.days"] * quicksum(self.q_iso_work[e,i] for i in self.days)
                - self.weights["isolated off self.days"] * quicksum(self.q_iso_off[e,i] for i in self.days)
                - self.weights["consecutive self.days"] * quicksum(self.q_con[e,i] for i in self.days)
                for e in  self.employees
                ), name="objective_function_restriction")
                    #- weights["backward rotation"] * k[e,i]
                    #+weights["preferences"] * quicksum(pref[e,t] for t in time_periods) * quicksum(self.y[c,e,t] for c in self.competencies)
        self.model.addConstrs((
            self.g_plus - self.g_minus 
            <= self.f_plus[e] - self.f_minus[e] 
            for e in self.employees)
            , name="lowest_fairness_score")
                

    def set_objective(self):
        self.model.setObjective(
                    quicksum(self.f_plus[e] - self.f_minus[e] for e in self.employees)
                    + self.weights["lowest fairness score"] * (self.g_plus - self.g_minus)
                    - self.weights["demand_deviation"] *
                    quicksum(
                        quicksum(
                            self.delta_plus[c, t] + self.delta_minus[c, t] for t in self.time_periods
                    ) for c in self.competencies
                    )
                    ,GRB.MAXIMIZE)



        print("#############RESTRICTIONS ADDED#############")


def main():
    model = Optimization_model()
    model.add_variables()
    model.add_constraints()
    model.set_objective()

    model.model.optimize()




if __name__ == "__main__":
    main()


