

class ALNS:

    def __init__(self, state, random_state=None):
        """

        :param random_state: provides consistent random data to ensure a deterministic output over different runs
        """

        self.state = state

        self.destroy_operators = {}
        self.repair_operators = {}

        self.random_state = random_state

        self.destroy_weights = self.initialize_weights(self.destroy_operators)
        self.repair_weights = self.initialize_weights(self.repair_operators)

    def solve(self):
        raise NotImplementedError

    def consider_solution(self):
        raise NotImplementedError

    def add_destroy_operator(self, operator):
        self.add_operator(self.destroy_operators, operator)

    def add_repair_operator(self, operator):
        self.add_operator(self.repair_operators, operator)

    def validate_parameters(self):
        raise NotImplementedError

    @staticmethod
    def add_operator(operators, new_operator):
        operators[new_operator.__name__] = new_operator

    @staticmethod
    def initialize_weights(operators):
        return operators
