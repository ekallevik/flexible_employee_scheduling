import numpy as np
from heuristic.heuristic_calculations import *
#from heuristic.utils import WeightUpdate


class ALNS:
    def __init__(self, state, model):

        self.initial_solution = state
        self.current_solution = state
        self.best_solution = state

        #self.criterion = criterion
        
        self.destroy_operators = {}
        self.destroy_weights = {}
        self.repair_operators = {}
        self.repair_weights = {}

        #Sets
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


    def iterate(self, iterations):
        for iteration in range(iterations):
            #destroy_operator = self.select_operator(self.destroy_operators, self.destroy_weights)
            #repair_operator = self.select_operator(self.repair_operators, self.repair_weights)
            candidate_solution = self.current_solution.copy()
            #destroyed_set = destroy_operator(candidate_solution, sets)
            #repair_set = repair_operator(candidate_solution, sets, destroyed_set)

            self.calculate_objective(candidate_solution)


    def consider_candidate_and_update_weights(self, candidate_solution, destroy_id, repair_id):
        pass

    def select_operator(self, operators, weights):
        pass


    def get_probabilities(self, weights):
        pass

    def update_weights(self, weight_update, destroy_id, repair_id):
        pass

    def initialize_destroy_and_repair_weights(self):
        pass

    def initialize_weights(self, operators):
        pass

    def initialize_random_state(self):
        pass

    def add_destroy_operator(self, operator):
        pass

    def add_repair_operator(self, operator):
        pass

    def calculate_objective(self, state):
        pass

    def add_operator(self, operators, new_operator):
        pass

    def initialize_state_variables(self, model):
        #Soft Variables
        negative_deviation_from_demand = calculate_negative_deviation_from_demand(model)
        partial_weekends = calculate_partial_weekends(model)
        consecutive_days = calculate_consecutive_days(model)
        isolated_off_days = calculate_isolated_off_days(model)
        isolated_working_days = calculate_isolated_working_days(model)
        contracted_hours = calculate_negative_deviation_from_contracted_hours(model)

        #Hard Penalty Variables
        cover_min_demand = cover_minimum_demand(model)
        cover_max_demand = under_maximum_demand(model)
        one_demand_per_time = cover_only_one_demand_per_time_period(model)
        one_shift_per_day = maximum_one_shift_per_day()
        one_weekly_off = one_weekly_off_shift(model)
        work_during_off = no_work_during_off_shift2(model)
        shift_demand_map = mapping_shift_to_demand(model)
        break_contracted_hours = calculate_positive_deviation_from_contracted_hours(model)