import numpy as np

from heuristic.utils import WeightUpdate


class ALNS:
    def __init__(self, state, criterion):

        self.initial_solution = state
        self.current_solution = state
        self.best_solution = state

        self.random_state = self.initialize_random_state()
        self.criterion = criterion

        self.destroy_operators = {}
        self.destroy_weights = {}
        self.repair_operators = {}
        self.repair_weights = {}

    def iterate(self, iterations):

        self.initialize_weights()

        for iteration in range(iterations):

            destroy_operator, destroy_id = self.select_operator(self.destroy_operators, self.destroy_weights)
            repair_operator, repair_id = self.select_operator(self.repair_operators, self.repair_weights)

            destroyed_solution = destroy_operator(self.current_solution)
            candidate_solution = repair_operator(destroyed_solution)

            self.consider_candidate_and_update_weights(candidate_solution, destroy_id, repair_id)

        return self.best_solution

    def consider_candidate_and_update_weights(self, candidate_solution, destroy_id, repair_id):
        # todo: this has potential for performance improvements, but unsure if it is only for GreedyCriterion

        if self.criterion.accept(candidate_solution, self.current_solution):
            self.current_solution = candidate_solution

            if candidate_solution.get_objectice_value() >= self.current_solution.get_objectice_value():
                weight_update = WeightUpdate.IS_BETTER
            else:
                weight_update = WeightUpdate.IS_ACCEPTED
        else:
            weight_update = WeightUpdate.IS_REJECTED

        if candidate_solution.get_objectice_value() >= self.best_solution.get_objective_value():

            # todo: this is copied from the Github-repo, but unsure if this is the correct way to do it.
            weight_update = WeightUpdate.IS_BEST
            self.best_solution = candidate_solution
            self.current_solution = candidate_solution

        self.update_weights(weight_update, destroy_id, repair_id)

    def update_weights(self, weight_update, destroy_id, repair_id):
        self.destroy_operators[destroy_id] *= weight_update
        self.repair_operators[repair_id] *= repair_id

    def select_operator(self, operators, weights):
        probabilities = self.get_probabilities(weights)
        selected_operator = self.random_state.choice(list(operators.keys()), p=probabilities)
        return selected_operator, selected_operator.__name__

    @staticmethod
    def get_probabilities(weights):
        total_weight = sum(weights.values())
        return [weight / total_weight for weight in weights.values()]

    def add_destroy_operator(self, operator):
        self.add_operator(self.destroy_operators, operator)

    def add_repair_operator(self, operator):
        self.add_operator(self.repair_operators, operator)

    @staticmethod
    def add_operator(operators, new_operator):

        if not callable(new_operator):
            raise ValueError("new_operator must be a function")

        operators[new_operator.__name__] = new_operator

    def initialize_weights(self):
        self.initialize_destroy_weights()

    def initialize_destroy_weights(self):

        if len(self.destroy_operators.keys()) == 0:
            raise ValueError("You cannot initialize weights before adding at least one operator")

        self.destroy_weights = {operator: 1.0 for operator in self.destroy_operators}

    def initialize_repair_weights(self):

        if len(self.repair_operators.keys()) == 0:
            raise ValueError("You cannot initialize weights before adding at least one operator")

        self.repair_weights = {operator: 1.0 for operator in self.repair_operators}

    @staticmethod
    def initialize_random_state():
        """ Provides a seeded random state to ensure a deterministic output over different runs """
        return np.random.RandomState(seed=0)
