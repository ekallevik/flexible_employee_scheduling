class Alns_calculator:

    def __init__(self, model):
        self.competencies = model.competencies
        self.demand = model.demand
        self.time_periods = model.time_periods
        self.employee_with_competencies = model.employee_with_competencies
        self.time_periods_in_day = model.time_periods_in_day
        self.contracted_hours = model.contracted_hours
        self.saturdays = model.saturdays
        self.employees = model.employees
        self.shifts_at_day = model.shifts_at_day
        self.L_C_D = model.L_C_D
        self.weeks = model.weeks
        self.off_shifts = model.off_shifts
        self.days = model.days
        self.time_step = model.time_step
        

    def calculate_deviation_from_demand(self, state):
        delta = {}
        for c in self.competencies:
            for t in self.time_periods:
                delta[c,t] = abs(sum(state.y[c,e,t] for e in self.employee_with_competencies[c]) - self.demand["ideal"][c,t])
        return delta


    def calculate_negative_deviation_from_demand(self, state, days=None):
        if(days == None):
            days = self.days
        delta = {}
        for c in self.competencies:
            for i in days:
                for t in self.time_periods_in_day[i]:
                    delta[c,t] = max(0, self.demand["ideal"][c,t] - sum(state.y[c,e,t] for e in self.employee_with_competencies[c]))
        return delta

    def calculate_negative_deviation_from_contracted_hours(self, state):
        delta_negative_contracted_hours = {}
        for e in self.employees:
            delta_negative_contracted_hours[e] = (len(self.weeks) * self.contracted_hours[e]
                - sum(self.time_step * state.y[c,e,t] 
                for t in self.time_periods
                for c in self.competencies))
        return delta_negative_contracted_hours

    def calculate_partial_weekends(self, state):
        partial_weekend = {}
        partial_weekend_shifts = []
        for i in self.saturdays:
            for e in self.employees:
                partial_weekend[e,i] =  abs(sum(state.x[e,t,v] 
                                        for t,v in self.shifts_at_day[i]) 
                                        - sum(state.x[e,t,v] 
                                        for t,v in self.shifts_at_day[i+1]))
        return partial_weekend


    def calculate_isolated_working_days(self, state):
        isolated_working_days = {}
        for e in self.employees:
            for i in range(len(self.days)-2):
                isolated_working_days[e,i+1] = max(0,(-sum(state.x[e,t,v] for t,v in self.shifts_at_day[i]) 
                + sum(state.x[e,t,v] for t,v in self.shifts_at_day[i+1]) 
                - sum(state.x[e,t,v] for t,v in self.shifts_at_day[i+2])))

        return isolated_working_days


    def calculate_isolated_off_days(self, state):
        isolated_off_days = {}
        for e in self.employees:
            for i in range(len(self.days)-2):
                isolated_off_days[e,i+1] = max(0,(sum(state.x[e,t,v] for t,v in self.shifts_at_day[i]) 
                - sum(state.x[e,t,v] for t,v in self.shifts_at_day[i+1]) 
                + sum(state.x[e,t,v] for t,v in self.shifts_at_day[i+2])-1))
        return isolated_off_days


    def calculate_consecutive_days(self, state):
        consecutive_days = {}
        for e in self.employees:
            for i in range(len(self.days)-self.L_C_D):
                consecutive_days[e,i] = max(0,(sum(
                    sum(state.x[e,t,v] for t,v in self.shifts_at_day[i_marked]) 
                for i_marked in range(i,i+self.L_C_D)))- self.L_C_D)
        return consecutive_days

    def calculate_f(self, state, employees=None):
        if(employees == None):
            employees = self.employees
        f = {}
        for e in employees:
            f[e] = (sum(v * state.w[e,t,v] for t,v in self.off_shifts)
                - state.contracted_hours[e]
                - sum(state.partial_weekend[e,i] for i in self.saturdays)
                - sum(state.q_iso_work[e,i+1] for i in range(len(self.days)-2))
                - sum(state.q_iso_off[e,i+1] for i in range(len(self.days)-2))
                - sum(state.q_con[e,i] for i in range(len(self.days)-self.L_C_D)))
        return f

    def calculate_objective_function(self, state):
        f = self.calculate_f(state)
        g = min(f.values())
        #Regular objective function
        objective = (sum(f[e] for e in self.employees)
                        + g
                        - sum(state.deviation_from_demand[c,t] for t in self.time_periods for c in self.competencies))
        return objective