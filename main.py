from model.feasibility_model import FeasibilityModel
from model.optimality_model import OptimalityModel


def main():

    esp = OptimalityModel("employee_scheduling_problem")
    esp.run_model()






if __name__ == "__main__":
    main()
