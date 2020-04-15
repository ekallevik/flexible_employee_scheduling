import numpy as np
from heuristic.heuristic_calculations import calculate_objective_function as calc_ob
#from heuristic.destroy_algorithms import remove_isolated_working_day, remove_partial_weekends
from heuristic.new_repair_algorithms import add_previously_isolated_days_randomly, add_previously_isolated_days_greedy, add_random_weekends, add_greedy_weekends
from heuristic.new_destroy_algorithms import remove_partial_weekends, remove_isolated_working_day
from heuristic.utils import WeightUpdate
from heuristic.delta_calculations import *
from heuristic.criterions.greedy_criterion import GreedyCriterion


class ALNS:
    def __init__(self, state, model, ):
        self.initial_solution = state
        self.current_solution = state
        self.best_solution = state

        self.criterion = GreedyCriterion()
        self.random_state =  self.initialize_random_state()
        
        self.destroy_operators = {}
        self.destroy_weights = {}
        self.repair_operators = {}
        self.repair_weights = {}

        self.WeightUpdate = {
            "IS_BEST": 1.3,
            "IS_BETTER": 1.2,
            "IS_ACCEPTED": 1.1,
            "IS_REJECTED": 0.9
        }


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
        self.off_shift_in_week = model.off_shift_in_week
        self.days = model.days
        self.time_step = model.time_step
        self.t_covered_by_shift = model.t_covered_by_shift
        self.shifts_overlapping_t = model.shifts_overlapping_t
        self.t_covered_by_off_shift = model.t_in_off_shifts


        self.add_destroy_operator([remove_partial_weekends, remove_isolated_working_day])
        self.add_repair_operator([add_previously_isolated_days_randomly, add_previously_isolated_days_greedy, add_random_weekends, add_greedy_weekends])
        self.initialize_destroy_and_repair_weights()


    def iterate(self, iterations):

        for iteration in range(iterations):
            destroy_operator = self.destroy_operators["remove_isolated_working_day"]
            repair_operator = self.repair_operators["add_previously_isolated_days_greedy"]
            #destroy_operator = self.select_operator(self.destroy_operators, self.destroy_weights)
            #repair_operator = self.select_operator(self.repair_operators, self.repair_weights)
            candidate_solution = self.current_solution.copy()
            #print(candidate_solution.soft_vars["partial_weekends"])
            iso_working_days, destroy_set = destroy_operator(candidate_solution, {"shifts_at_day":self.shifts_at_day, "t_covered_by_shift":self.t_covered_by_shift})
            #print(str(destroy_set) + "\n")
            #print(candidate_solution.soft_vars["isolated_working_days"])
            #partial_weekends, destroy_set = destroy_operator(candidate_solution, {"shifts_at_day":self.shifts_at_day, "t_covered_by_shift":self.t_covered_by_shift})
            #repair_set = repair_operator(candidate_solution, {"saturdays":self.saturdays, "shifts_at_day":self.shifts_at_day, "t_covered_by_shift":self.t_covered_by_shift, "competencies": self.competencies}, partial_weekends)
            repair_set = repair_operator(candidate_solution, {"shifts_at_day":self.shifts_at_day, "t_covered_by_shift":self.t_covered_by_shift, "competencies": self.competencies, "employees": self.employees}, iso_working_days, destroy_set)
            self.calculate_objective(candidate_solution, destroy_set, repair_set)
            #print(repair_set)
            #print(candidate_solution.soft_vars["negative_deviation_from_demand"])
            #print([(e,t,v) for e,t,v in candidate_solution.x if candidate_solution.x[e,t,v] == 1])
            #print(candidate_solution.soft_vars["contracted_hours"])
            #print(candidate_solution.hard_vars["delta_positive_contracted_hours"])
            self.consider_candidate_and_update_weights(candidate_solution, destroy_operator.__name__, repair_operator.__name__)
        candidate_solution.write("heuristic_solution")
        print(candidate_solution.soft_vars["isolated_working_days"])
            

    def consider_candidate_and_update_weights(self, candidate_solution, destroy_id, repair_id):
        """
        Considers the candidate based on self.critertion, and will update the weights according to the outcome
        :param candidate_solution: The solution to consider
        :param destroy_id: the id (name) of the destroy function used to create this state
        :param repair_id: the id (name) of the repair function used to create this state
        """
        # todo: this has potential for performance improvements, but unsure if it is only for GreedyCriterion
        print(str(candidate_solution.get_objective_value()) + " VS " + str(self.current_solution.get_objective_value()))
        if self.criterion.accept(candidate_solution, self.current_solution):
            self.current_solution = candidate_solution

            if candidate_solution.get_objective_value() >= self.current_solution.get_objective_value():
                weight_update = self.WeightUpdate["IS_BETTER"]
            else:
                weight_update = self.WeightUpdate["IS_ACCEPTED"]
        else:
            weight_update = self.WeightUpdate["IS_REJECTED"]

        if candidate_solution.get_objective_value() >= self.best_solution.get_objective_value():

            # todo: this is copied from the Github-repo, but unsure if this is the correct way to do it.
            weight_update = self.WeightUpdate["IS_BEST"]
            self.best_solution = candidate_solution
            self.current_solution = candidate_solution
        self.update_weights(weight_update, destroy_id, repair_id)

    def select_operator(self, operators, weights):
        """
        Randomly selects an operator from a probability distribution based on the operators weights.
        :param operators: self.destroy_operators or self.repair_operators
        :param weights: the weights associated with the operators
        :return: the operator function, and it´s ID.
        """

        probabilities = self.get_probabilities(weights)
        selected_operator_id = self.random_state.choice(list(operators.keys()), p=probabilities)
        return operators[selected_operator_id], selected_operator_id

    @staticmethod
    def get_probabilities(weights):
        total_weight = sum(weights.values())
        return [weight / total_weight for weight in weights.values()]


    def update_weights(self, weight_update, destroy_id, repair_id):
        """ Updates the value of the operator pair by multiplying both with weight_update """

        self.destroy_weights[destroy_id] *= weight_update
        self.repair_weights[repair_id] *= weight_update

    def initialize_destroy_and_repair_weights(self):
        self.destroy_weights = self.initialize_weights(self.destroy_operators)
        self.repair_weights = self.initialize_weights(self.repair_operators)

    @staticmethod
    def initialize_weights(operators):

        if not operators:
            raise ValueError("You cannot initialize weights before adding at least one operator")

        return {operator: 1.0 for operator in operators}

    @staticmethod
    def initialize_random_state():
        """ Provides a seeded random state to ensure a deterministic output over different runs """
        return np.random.RandomState(seed=0)

    def add_destroy_operator(self, operators):
        for operator in operators:
            self.add_operator(self.destroy_operators, operator)

    def add_repair_operator(self, operators):
        for operator in operators:
            self.add_operator(self.repair_operators, operator)

    @staticmethod
    def add_operator(operators, new_operator):
        """
        Adds a new operator to the given set. If new_operator is not a function a ValueError is raised.
        :param operators: either self.destroy_operators or self.repair_operators
        :param new_operator: the operator to add to the sets
        """

        if not callable(new_operator):
            raise ValueError("new_operator must be a function")

        operators[new_operator.__name__] = new_operator

    def calculate_objective(self, state, destroy, repair):
        destroy_repair_set = destroy + repair
        employees = set([e for e,t,v in destroy_repair_set])

        #Updates the current states soft variables based on changed decision variables
        delta_calculate_deviation_from_demand(state, self.competencies, self.t_covered_by_shift, self.employee_with_competencies, self.demand, destroy_repair_set)
        delta_calculate_negative_deviation_from_contracted_hours(state, repair, destroy, employees, self.contracted_hours, self.weeks, self.time_periods, self.competencies, self.time_step)
        calculate_partial_weekends(state, employees, self.shifts_at_day, self.saturdays)
        calculate_isolated_working_days(state, employees, self.shifts_at_day, self.days)
        calculate_isolated_off_days(state, employees, self.shifts_at_day, self.days)
        calculate_consecutive_days(state, employees, self.shifts_at_day, self.L_C_D, self.days)

        #Updates the current states hard variables based on changed decision variables
        below_minimum_demand(state, destroy_repair_set, self.employee_with_competencies, self.demand, self.time_periods, self.competencies, self.t_covered_by_shift)
        above_maximum_demand(state, destroy_repair_set, self.employee_with_competencies, self.demand, self.time_periods, self.competencies, self.t_covered_by_shift)
        more_than_one_shift_per_day(state, destroy_repair_set, self.demand, self.shifts_at_day, self.days)
        cover_multiple_demand_periods(state, repair, self.t_covered_by_shift, self.competencies)
        weekly_off_shift_error(state, destroy_repair_set, self.weeks, self.off_shift_in_week)
        no_work_during_off_shift(state, destroy_repair_set, self.competencies, self.t_covered_by_off_shift, self.off_shifts)
        mapping_shift_to_demand(state, destroy_repair_set, self.t_covered_by_shift, self.shifts_overlapping_t, self.competencies)
        #calculate_positive_deviation_from_contracted_hours(state, destroy, repair)


        return calculate_objective_function(state, employees, self.off_shifts, self.saturdays, self.L_C_D, self.days, self.competencies)

    # def initialize_state_variables(self, model):
    #     #Soft Variables
    #     negative_deviation_from_demand = calculate_negative_deviation_from_demand(model)
    #     partial_weekends = calculate_partial_weekends(model)
    #     consecutive_days = calculate_consecutive_days(model)
    #     isolated_off_days = calculate_isolated_off_days(model)
    #     isolated_working_days = calculate_isolated_working_days(model)
    #     contracted_hours = calculate_negative_deviation_from_contracted_hours(model)

    #     #Hard Penalty Variables
    #     cover_min_demand = cover_minimum_demand(model)
    #     cover_max_demand = under_maximum_demand(model)
    #     one_demand_per_time = cover_only_one_demand_per_time_period(model)
    #     one_shift_per_day = maximum_one_shift_per_day()
    #     one_weekly_off = one_weekly_off_shift(model)
    #     work_during_off = no_work_during_off_shift2(model)
    #     shift_demand_map = mapping_shift_to_demand(model)
    #     break_contracted_hours = calculate_positive_deviation_from_contracted_hours(model)