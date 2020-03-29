class ALNS:
    def __init__(self, state, random_state=None):
        """

        :param random_state: provides consistent random data to ensure a deterministic output over different runs
        """

        self.state = state
        self.random_state = random_state

        self.destroy_operators = {}
        self.repair_operators = {}

        self.destroy_weights = {}
        self.repair_weights = {}

    def solve(self):

        self.initialize_weights()

        raise NotImplementedError

    def consider_solution(self):
        raise NotImplementedError

    def add_destroy_operator(self, operator):
        self.add_operator(self.destroy_operators, operator)

    def add_repair_operator(self, operator):
        self.add_operator(self.repair_operators, operator)

    @staticmethod
    def add_operator(operators, new_operator):
        operators[new_operator.__name__] = new_operator

    def initialize_weights(self):
        self.initialize_destroy_weights()

    def initialize_destroy_weights(self):

        if len(self.destroy_operators.keys()) == 0:
            raise ValueError("You cannot initialize weights before adding at least one operator")

        weight = 1.0 / len(self.destroy_operators.keys())
        self.destroy_weights = {operator: weight for operator in self.destroy_operators}

    def initialize_repair_weights(self):

        if len(self.repair_operators.keys()) == 0:
            raise ValueError("You cannot initialize weights before adding at least one operator")

        weight = 1.0 / len(self.repair_operators.keys())
        self.repair_weights = {operator: weight for operator in self.repair_operators}
