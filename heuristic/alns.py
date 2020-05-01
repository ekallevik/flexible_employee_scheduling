from functools import partial

import numpy as np

from heuristic.delta_calculations import *
from heuristic.destroy_operators import (worst_employee_removal,
                                         worst_week_removal)
from heuristic.local_search_operators import illegal_week_swap
from heuristic.repair_operators import (worst_employee_regret_repair,
                                        worst_employee_repair,
                                        worst_week_regret_repair,
                                        worst_week_repair)


class ALNS:
    def __init__(self, state, model, criterion, data):
        self.initial_solution = state
        self.current_solution = state
        self.best_solution = state
        self.best_legal_solution = state

        self.criterion = criterion
        self.random_state = self.initialize_random_state()

        self.destroy_operators = {}
        self.destroy_weights = {}
        self.repair_operators = defaultdict(dict)
        self.repair_weights = {}

        self.WeightUpdate = {
            "IS_BEST": 1.3,
            "IS_BETTER": 1.2,
            "IS_ACCEPTED": 1.1,
            "IS_REJECTED": 0.9,
        }

        # Sets
        self.competencies = data["competencies"]
        self.demand = data["demand"]

        self.days = data["time"]["days"]
        self.weeks = data["time"]["weeks"]
        self.saturdays = data["time"]["saturdays"]
        self.time_step = data["time"]["step"]
        self.time_periods = data["time"]["periods"][0]
        self.time_periods_in_week = data["time"]["periods"][1]
        self.time_periods_in_day = data["time"]["periods"][2]
        self.t_covered_by_shift = data["heuristic"]["t_covered_by_shift"]

        self.shifts = data["shifts"]["shifts"]

        self.employees = data["staff"]["employees"]
        self.employee_with_competencies = data["staff"]["employees_with_competencies"]
        self.contracted_hours = data["staff"]["employee_contracted_hours"]

        self.shifts_at_day = data["shifts"]["shifts_per_day"]
        self.off_shifts = data["off_shifts"]["off_shifts"]
        self.off_shift_in_week = data["off_shifts"]["off_shifts_per_week"]
        self.t_covered_by_shift = data["heuristic"]["t_covered_by_shift"]
        self.shifts_overlapping_t = data["shifts"]["shifts_overlapping_t"]

        self.L_C_D = data["limit_on_consecutive_days"]

        self.shifts_per_week = data["shifts"]["shifts_per_week"]

        # todo: these seems to be unused. Delete?
        self.sundays = data["time"]["sundays"]
        self.shift_lookup = data["heuristic"]["shift_lookup"]
        self.shifts_covered_by_off_shift = data["shifts"]["shifts_covered_by_off_shift"]





        remove_worst_week = partial(
            worst_week_removal,
            self.competencies,
            self.time_periods_in_week,
            self.employees,
            self.weeks,
            self.L_C_D,
            self.shifts_per_week,
            self.t_covered_by_shift,
        )
        remove_worst_employee = partial(
            worst_employee_removal, self.shifts, self.t_covered_by_shift
        )

        repair_worst_week_regret = partial(
            worst_week_regret_repair,
            self.shifts_per_week,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.demand,
            self.time_step,
            self.time_periods_in_week,
            self.employees,
            self.contracted_hours,
            self.weeks,
            self.shifts_at_day,
            self.L_C_D,
            self.shifts_overlapping_t,
        )

        repair_worst_employee_regret = partial(
            worst_employee_regret_repair,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.demand,
            self.shifts,
            self.off_shifts,
            self.saturdays,
            self.days,
            self.L_C_D,
            self.weeks,
            self.shifts_at_day,
            self.shifts_per_week,
            self.contracted_hours,
            self.time_periods_in_week,
            self.time_step,
            self.shifts_overlapping_t,
        )

        repair_worst_week_greedy = partial(
            worst_week_repair,
            self.shifts_per_week,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.demand,
            self.time_step,
            self.time_periods_in_week,
            self.employees,
            self.contracted_hours,
            self.weeks,
            self.shifts_at_day,
        )

        repair_worst_employee_greedy = partial(
            worst_employee_repair,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.demand,
            self.contracted_hours,
            self.weeks,
            self.time_periods_in_week,
            self.time_step,
            self.shifts,
            self.shifts_at_day,
        )

        operators = {
            remove_worst_employee: [repair_worst_employee_regret, repair_worst_employee_greedy],
            remove_worst_week: [repair_worst_week_regret, repair_worst_week_greedy],
        }
        self.add_destroy_and_repair_operators(operators)
        self.initialize_destroy_and_repair_weights()

    def iterate(self, iterations):
        """	
            Mostly the same structure as Even had put up. Start by selecting a destroy and repair operator.	
            I have not used the select function as I only test one at a time here. The select function do work though.	
            The destroy and repair operators are commented out on purpose as I have decided to include these in another PR	
            Candidate solution is created by copying the current solution state.	
            Problem not fixed is how to send the correct sets together with the destroy and repair operator. 	
            All my destroy operators have two values they are returning:	
                1. A destroy set that includes shifts (e,t,v) that are destroyed	
                2. Some spesific information about what were destroyed for example weeks, isolated days and so on. 	
            Calculate objective function is new. It is in charge of updating the soft variables, hard variables, f and objective function	
            based on the destroy and repair operator (the shifts that were destroyed and repaired)	
            Lastly consider candidate is run.	
        """
        for iteration in range(iterations):
            candidate_solution = self.current_solution.copy()

            destroy_operator, destroy_operator_id = self.select_operator(
                self.destroy_operators, self.destroy_weights
            )
            repair_operator, repair_operator_id = self.select_operator(
                self.repair_operators[destroy_operator_id], self.repair_weights[destroy_operator_id]
            )

            destroy_set, destroy_spesific_set = destroy_operator(candidate_solution)
            repair_set = repair_operator(candidate_solution, destroy_set, destroy_spesific_set)

            self.calculate_objective(candidate_solution, destroy_set, repair_set)
            self.consider_candidate_and_update_weights(
                candidate_solution, destroy_operator_id, repair_operator_id
            )

        candidate_solution.write("heuristic_solution_2")

    def consider_candidate_and_update_weights(self, candidate_solution, destroy_id, repair_id):
        """
        Considers the candidate based on self.critertion, and will update the weights according to the outcome
        :param candidate_solution: The solution to consider
        :param destroy_id: the id (name) of the destroy function used to create this state
        :param repair_id: the id (name) of the repair function used to create this state
        """
        # todo: this has potential for performance improvements, but unsure if it is only for GreedyCriterion
        print(
            str(candidate_solution.get_objective_value())
            + " VS "
            + str(self.current_solution.get_objective_value())
        )
        if self.criterion.accept(candidate_solution, self.current_solution, self.random_state):
            self.current_solution = candidate_solution

            # Local search operator runs within this if statement. A better implementation should be decided on.
            if sum(candidate_solution.hard_vars["weekly_off_shift_error"].values()) != 0:
                candidate_solution.write("before_breaking_weekly")
                destroy_set, repair_set = illegal_week_swap(
                    self.shifts_per_week,
                    self.employees,
                    self.shifts_at_day,
                    self.t_covered_by_shift,
                    self.competencies,
                    self.contracted_hours,
                    self.time_periods_in_week,
                    self.time_step,
                    self.L_C_D,
                    self.weeks,
                    candidate_solution,
                )
                self.calculate_objective(candidate_solution, destroy_set, repair_set)
                candidate_solution.write("After_breaking_weekly")

            if (
                candidate_solution.get_objective_value()
                >= self.best_legal_solution.get_objective_value()
                and hard_constraint_penalties(candidate_solution) == 0
            ):
                self.best_legal_solution = candidate_solution
                print("Is legal")
                self.best_legal_solution.write("best_legal_solution")

            if (
                candidate_solution.get_objective_value()
                >= self.current_solution.get_objective_value()
            ):
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
            self.best_solution.write("heuristic_solution_2")
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
        self.repair_weights[destroy_id][repair_id] *= weight_update

    def initialize_destroy_and_repair_weights(self):
        self.destroy_weights = self.initialize_weights(self.destroy_operators)
        for destroy_operator in self.destroy_operators:
            self.repair_weights[destroy_operator] = self.initialize_weights(
                self.repair_operators[destroy_operator]
            )

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

    # Removed the old add repair operator function. Left here for ease of access and understandability.
    # def add_repair_operator(self, operators):
    #   for operator in operators:
    #      self.add_operator(self.repair_operators, operator)

    def add_repair_operator(self, destroy_operator_id, repair_operators):
        for new_operator in repair_operators:
            self.repair_operators[destroy_operator_id][new_operator.func.__name__] = new_operator

    def add_destroy_and_repair_operators(self, operators):
        for key in operators.keys():
            self.add_destroy_operator([key])
            self.add_repair_operator(key.func.__name__, operators[key])

    @staticmethod
    def add_operator(operators, new_operator):
        """
        Adds a new operator to the given set. If new_operator is not a function a ValueError is raised.
        :param operators: either self.destroy_operators or self.repair_operators
        :param new_operator: the operator to add to the sets
        """

        if not callable(new_operator):
            raise ValueError("new_operator must be a function")

        operators[new_operator.func.__name__] = new_operator

    def calculate_objective(self, state, destroy, repair):
        destroy_repair_set = destroy + repair
        employees = set([e for e, t, v in destroy_repair_set])

        # Updates the current states soft variables based on changed decision variables
        calculate_deviation_from_demand(
            state,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.demand,
            destroy_repair_set,
        )
        delta_calculate_negative_deviation_from_contracted_hours(
            state,
            employees,
            self.contracted_hours,
            self.weeks,
            self.time_periods_in_week,
            self.competencies,
            self.time_step,
        )
        calculate_partial_weekends(state, employees, self.shifts_at_day, self.saturdays)
        calculate_isolated_working_days(state, employees, self.shifts_at_day, self.days)
        calculate_isolated_off_days(state, employees, self.shifts_at_day, self.days)
        calculate_consecutive_days(state, employees, self.shifts_at_day, self.L_C_D, self.days)
        calculate_weekly_rest(state, self.shifts_per_week, employees, self.weeks)

        # Updates the current states hard variables based on changed decision variables
        below_minimum_demand(
            state,
            destroy_repair_set,
            self.employee_with_competencies,
            self.demand,
            self.competencies,
            self.t_covered_by_shift,
        )
        above_maximum_demand(
            state,
            destroy_repair_set,
            self.employee_with_competencies,
            self.demand,
            self.competencies,
            self.t_covered_by_shift,
        )
        more_than_one_shift_per_day(state, employees, self.demand, self.shifts_at_day, self.days)
        cover_multiple_demand_periods(state, repair, self.t_covered_by_shift, self.competencies)
        mapping_shift_to_demand(
            state,
            destroy_repair_set,
            self.t_covered_by_shift,
            self.shifts_overlapping_t,
            self.competencies,
        )

        # I believe these functions comment out below are not needed. If by your understanding you agree we can remove them.

        # calculate_positive_deviation_from_contracted_hours(state, destroy, repair)
        # weekly_off_shift_error(state, destroy_repair_set, self.weeks, self.off_shift_in_week)
        # no_work_during_off_shift(state, destroy_repair_set, self.competencies, self.t_covered_by_off_shift, self.off_shifts)

        return calculate_objective_function(
            state,
            employees,
            self.off_shifts,
            self.saturdays,
            self.L_C_D,
            self.days,
            self.competencies,
            self.weeks,
        )
