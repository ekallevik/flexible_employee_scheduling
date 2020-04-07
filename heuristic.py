from model.feasibility_model import FeasibilityModel
from model.optimality_model import OptimalityModel
from heuristic_calculations import *
from repair_algorithms import *
from destroy_algorithms import *
from converter import convert





def main():
    model = FeasibilityModel("esp", "rproblem2")
    model.run_model()
    x,y,w = convert(model) 
    model.x = x
    model.y = y
    model.w = w
    print("############## Objective Function ##############")
    print(calculate_objective_function(model))


if __name__ == "__main__":
    main()