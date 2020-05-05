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
        """
        Performs the given number of iterations of ALNS by successively destroy and then repair the current solution

        :param iterations: the number of iterations
        :return: the best solution found
        """

        # todo: this initialization can be moved to a better place, but need an integrated method for setting operators
        # before this method is called. If the operators are not initialized this method will raise DivisionByZeroError
        self.initialize_destroy_and_repair_weights()

        for iteration in range(iterations):

            destroy_operator, destroy_id = self.select_operator(
                self.destroy_operators, self.destroy_weights
            )
            repair_operator, repair_id = self.select_operator(
                self.repair_operators, self.repair_weights
            )

            destroyed_solution = destroy_operator(self.current_solution)
            candidate_solution = repair_operator(destroyed_solution)

            self.consider_candidate_and_update_weights(candidate_solution, destroy_id, repair_id)


    def consider_candidate_and_update_weights(self, candidate_solution, destroy_id, repair_id):
        """
        Considers the candidate based on self.critertion, and will update the weights according to the outcome

        :param candidate_solution: The solution to consider
        :param destroy_id: the id (name) of the destroy function used to create this state
        :param repair_id: the id (name) of the repair function used to create this state
        """

        # todo: this has potential for performance improvements, but unsure if it is only for GreedyCriterion

        if self.criterion.accept(candidate_solution, self.current_solution, self.random_state):
            self.current_solution = candidate_solution

            if (
                candidate_solution.get_objectice_value()
                >= self.current_solution.get_objectice_value()
            ):
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

    def add_destroy_operator(self, operator):
        self.add_operator(self.destroy_operators, operator)

    def add_repair_operator(self, operator):
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
