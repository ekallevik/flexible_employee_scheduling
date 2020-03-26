class Converter:
    def __init__(self, gurobi_model):

        self.gurobi_variables = self.get_gurobi_variables(gurobi_model)

        self.x = self.convert_x()
        self.y = self.convert_y()
        self.w = self.convert_w()

    # todo: dict or args?
    def get_converted_variables(self):
        return self.x, self.y, self.y

    def convert_x(self):
        """
        Converts the x-variable to a simple dict.
        Could be swapped with NumPy or Pandas in future work
        """

        var = self.gurobi_variables
        return {(e, t, v): abs(var.x[e, t, v].x) for e, t, v in var.x}

    def convert_y(self):
        """
        Converts the y-variable to a simple dict.
        Could be swapped with NumPy or Pandas in future work
        """

        var = self.gurobi_variables
        return {(c, e, t): abs(var.y[c, e, t].x) for c, e, t in var.y}

    def convert_w(self):
        """
        Converts the w-variable to a simple dict.
        Could be swapped with NumPy or Pandas in future work
        """

        var = self.gurobi_variables
        return {(e, t, v): abs(var.w[e, t, v].x) for e, t, v in var.w}

    @staticmethod
    def get_gurobi_variables(gurobi_model):
        return gurobi_model.var
