class Converter:
    def __init__(self, gurobi_solution):

        self.gurobi_variables = gurobi_solution.get_variables()

        self.x = self.convert(self.gurobi_variables.x)
        self.y = self.convert(self.gurobi_variables.y)
        self.w = self.convert(self.gurobi_variables.w)

    def get_converted_variables(self):
        return {"x": self.x, "y": self.y, "w": self.w}

    @staticmethod
    def convert(var):

        key_tuples = var.keys()

        if len(key_tuples[0]) != 3:
            raise ValueError("This variable is not a 3D dict")

        converted_dict = {}

        for key1, key2, key3 in key_tuples:

            # if the 1st dict does not exists, create it
            if key1 not in converted_dict:
                converted_dict[key1] = {}

            # if the 2nd dict does not exist, create it
            if key2 not in converted_dict[key1]:
                converted_dict[key1][key2] = {}

            # if the 3rd dict does not exist, create it
            if key3 not in converted_dict[key1][key2]:
                converted_dict[key1][key2][key3] = {}

            # Make sure that values are always positive
            converted_dict[key1][key2][key3] = abs(var[key1, key2, key3].x)

        return converted_dict
