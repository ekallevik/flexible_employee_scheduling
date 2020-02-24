import gurobipy
import xml_loader.xml_loader
#MODEL
model = Model("Employee_scheduling_haakon")


#SETS



#Variables
#y = model.addVars(competencies, employees, time_periods, vtype=GRB.BINARY, name='y')




"""
def objective_restriction(self):
    self.model.addConstrs((
        self.f[e] ==  
            self.weight_contract * self.l[e]
            - self.weight_weekends * 
                quicksum(self.ro_sat[e,j] + self.ro_sun[e,j] 
                for j in self.saturdays)
            + 2*self.weight_preferences[e] * 
                quicksum(
                        self.preferences[e,t]*
                        quicksum(
                                self.y[c,e,t] 
                                for c in self.competencies)
                        for t in self.time_periods)
            + self.weight_rest * 
                quicksum(
                    quicksum(
                        quicksum(
                            (v - self.employee_rest_weekly[e]) * self.z[e,t,v]
                            for t in self.all_time_periods
                        if t >= self.offset_week_employee[e]+j*self.hours_in_week 
                        and t < self.offset_week_employee[e]+(j+1)*self.hours_in_week-(v))
                        for v in self.weekly_off_durations)
                    for j in self.weeks
                    )
            - self.weight_consecutive_days * 
                quicksum(
                    self.q_con[e,i] 
                    for i in self.days)
            - self.weight_isolated_work * 
                quicksum(
                    self.q_iso_work[e,i] 
                    for i in self.days)
            - self.weight_isolated_off *
                quicksum(
                    self.q_iso_off[e,i] 
                    for i in self.days)
            - self.weight_rot * 
                quicksum(
                    self.gamma[e,i] 
                    for i in self.days)
    for e in self.employees),
    name="objective_function_restriction")


    self.model.addConstrs((
        self.g <= self.f[e] for e in self.employees)
        ,name="lowest_fairness_score")

def add_variables(self):
    self.x = self.model.addVars(self.employees, self.shifts_work, self.time_periods, self.work_durations, vtype=GRB.BINARY, name='x')
    self.w = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='w')
    self.ro_sat = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='ro_sat')
    self.ro_sun = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='ro_sun')
    self.z = self.model.addVars(self.employees, self.all_time_periods, self.off_durations, vtype=GRB.BINARY, name='z')
    self.gamma = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='gamma')
    self.q_con = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='q_con')
    self.q_iso_off = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='q_iso_off')
    self.q_iso_work = self.model.addVars(self.employees, self.days, vtype=GRB.BINARY, name='q_iso_work')
    self.mu = self.model.addVars(self.competencies, self.shifts_work, self.time_periods, vtype=GRB.INTEGER, name='mu')
    self.l = self.model.addVars(self.employees,vtype=GRB.INTEGER, name='lambda')
    self.delta_plus = self.model.addVars(self.competencies, self.shifts_work, self.time_periods, vtype=GRB.INTEGER, name='delta_plus')
    self.delta_minus = self.model.addVars(self.competencies, self.shifts_work, self.time_periods, vtype=GRB.INTEGER, name='delta_minus')
    self.f = self.model.addVars(self.employees, vtype=GRB.CONTINUOUS, name='f')
    self.g = self.model.addVar(vtype=GRB.CONTINUOUS, name='g')

    self.model.update()
    #Set variable parameters

    #Used to fix the possible shift starting times to a number of predefined times. 
    #for key in self.fixed_shift_times:
        #   self.x[key].ub = 0

    for var in self.delta_plus:
        self.delta_plus[var].lb = 0
        self.delta_minus[var].lb = 0


    
    for key in self.x_dict.keys():
        self.x[key].ub = 0


def add_objective(self):
    self.model.setObjective(
        quicksum(self.f[e] for e in self.employees)
        + self.weight_lowest_fairness_score * self.g
        - self.weight_demand_deviation*
        quicksum(
            quicksum(
                quicksum(
                    self.delta_plus[c,s,t] + self.delta_minus[c,s,t] for t in self.time_periods
                ) for s in self.shifts_work
            ) for c in self.competencies
        )
        ,GRB.MAXIMIZE)
"""