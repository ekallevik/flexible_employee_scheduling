class Converter:
    def __init__(self, gurobi_solution):

        self.gurobi_variables = gurobi_solution.get_variables()
        self.model = gurobi_solution
        self.x = self.convert_x()
        self.y = self.convert_y()
        self.w = self.convert_w()

    def get_converted_variables(self):
        return {"x": self.x, "y": self.y, "w": self.w}

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
        return {(e,j): (t,v) for e in self.model.employees for j in self.model.weeks for t,v in self.model.off_shift_in_week[j] if var.w[e,t,v].x == 1}

