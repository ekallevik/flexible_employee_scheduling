import sys

import fire
from loguru import logger

from heuristic.alns import ALNS
from heuristic.criterions.greedy_criterion import GreedyCriterion
from heuristic.state import State
from model.construction_model import ConstructionModel
from model.feasibility_model import FeasibilityModel
from model.optimality_model import OptimalityModel
from model.shift_design_model import ShiftDesignModel
from preprocessing import shift_generation
from results.converter import Converter
from utils.log_formatter import LogFormatter

formatter = LogFormatter()

# Increase the level to get less output
level_per_module = {
    "__main__": "INFO",
    "preprocessing.xml_loader": "WARNING",
}

logger.remove()
logger.add(sys.stderr, format=formatter.format, filter=level_per_module)
logger.add("logs/log_{time}.log", format=formatter.format, retention="1 day")

class ProblemRunner:

    def __init__(self, problem="rproblem3", model="construction", with_sdp=True):

        self.problem = problem
        self.data = shift_generation.load_data(problem)
        self.model = model

        self.esp_solution = None
        self.alns_solution = None

        if with_sdp:
            self.run_shift_design_model()

    def run_heuristic(self):
        """

        :return:
        """

        self.run_model()

        converter = Converter(self.esp_solution)
        converted_solution = converter.get_converted_variables()

        state = State(converted_solution)
        criterion = GreedyCriterion()

        alns = ALNS(state, criterion)
        self.alns_solution = alns.iterate(iterations=1000)

        return self

    def run_model(self, model="construction"):
        """
        Runs the specified model on the given problem.

        :return: self
        """

        breakpoint()

        if model == "feasibility":
            esp = FeasibilityModel(name="esp_feasibility", problem=self.problem, data=self.data)
        elif model == "optimality":
            esp = OptimalityModel(name="esp_optimality", problem=self.problem, data=self.data)
        elif model == "construction":
            esp = ConstructionModel(name="esp_construction", problem=self.problem, data=self.data)
        else:
            raise ValueError(f"The model choice '{model}' is not valid.")

        breakpoint()

        esp.run_model()

        self.esp_solution = esp

        breakpoint()

        return self

    # TODO: how to ensure that this model only runs once?
    #  private method?
    #  switch flag?
    def run_shift_design_model(self):
        """
        Runs the shift design model.

        :return: self to enable chaining of Fire-commands
        """

        original_shifts = self.data["shifts"]["shifts"]

        breakpoint()

        sdp = ShiftDesignModel(name="sdp", data=self.data)
        sdp.run_model()

        used_shifts = sdp.get_used_shifts()
        self.data["shifts"] = shift_generation.get_updated_shift_sets(self.problem, self.data,
                                                                      used_shifts)

        print(f"SDP-reduction from {len(original_shifts)} to {len(used_shifts)} shift")
        percentage_reduction = (len(original_shifts) - len(used_shifts)) / len(original_shifts)
        print(f"This is a reduction of {100*percentage_reduction:.2f}%")

        breakpoint()

        return self


if __name__ == "__main__":
    """ 
    Run any function by using:
        python main.py FUNCTION_NAME *ARGS
    
    Reason for using class: Being able to pass in init-arguments as kwargs --arg=value
    
    Access property PROP by using: 
        python main.py FUNCTION_NAME PROP
        
    Chaining
        $ python example.py move 3 3 on move 3 6 on move 6 3 on move 6 6 on move 7 4 on move 7 5 on
        
        need to return self
        
        $ python example.py --name="Sherrerd Hall" --stories=3 climb_stairs 10
        $ python example.py --name="Sherrerd Hall" climb_stairs --stairs_per_story=10
        $ python example.py --name="Sherrerd Hall" climb_stairs --stairs-per-story 10
        $ python example.py climb-stairs --stairs-per-story 10 --name="Sherrerd Hall"
        
    Custom __str__
    
    """

    fire.Fire(ProblemRunner)
