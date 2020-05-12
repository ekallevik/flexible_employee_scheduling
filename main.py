import fire
from gurobipy import *
from loguru import logger

from heuristic.alns import ALNS
from heuristic.criterions.greedy_criterion import GreedyCriterion
from heuristic.heuristic_calculations import *
from heuristic.criterions.simulated_annealing_criterion import SimulatedAnnealingCriterion
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
# Trace < Info < Debug < Warning < Error < Critical
level_per_module = {
    "__main__": "INFO",
    "preprocessing.xml_loader": "WARNING",
    "heuristic.alns": "TRACE",
    "heuristic.destroy_operators": "TRACE",
    "heuristic.repair_operators": "TRACE",
}

logger.remove()
logger.add(sys.stderr, level="TRACE", format=formatter.format, filter=level_per_module)
logger.add("logs/log_{time}.log", format=formatter.format, retention="1 day")


class ProblemRunner:
    def __init__(self, problem="rproblem3", mode="feasibility", with_sdp=True):
        """
        Holds common data across all problems. Use --arg_name=arg_value from the terminal to
        use non-default values
        """

        logger.info(f"Setting up runner for {problem}")

        self.problem = problem
        self.data = shift_generation.load_data(problem)

        # Standard Gurobi-config
        self.mip_focus = "default"
        self.solution_limit = "default"
        self.log_to_console = 1

        self.sdp = None
        if with_sdp:
            self.set_sdp()
            self.run_sdp()

        self.mode = mode
        self.esp = None

        self.criterion = GreedyCriterion()
        self.alns = None

        self.set_esp()

    def run_alns(self, iterations=1000):
        """ Runs ALNS on the generated candidate solution """

        self.set_alns()

        logger.info(f"Running ALNS with {iterations} iterations and {self.criterion}")
        self.alns.iterate(iterations)

        return self

    def change_criterion(self, start_temp=100, end_temp=1, step=1, method="linear"):
        """ Changes the criterion to Simulated Annealing"""

        self.criterion = SimulatedAnnealingCriterion(
            method=method, start_temperature=start_temp, end_temperature=end_temp, step=step
        )

        return self

    def set_alns(self):
        """ Sets ALNS based on the given config """

        candidate_solution = self.get_candidate_solution()

        soft_variables = {
            "deviation_from_ideal_demand": calculate_deviation_from_demand(
                self.data, candidate_solution["y"]
            ),
            "partial_weekends": calculate_partial_weekends(self.data, candidate_solution["x"]),
            "consecutive_days": calculate_consecutive_days(self.data, candidate_solution["x"]),
            "isolated_off_days": calculate_isolated_off_days(self.data, candidate_solution["x"]),
            "isolated_working_days": calculate_isolated_working_days(
                self.data, candidate_solution["x"]
            ),
            "deviation_contracted_hours": calculate_negative_deviation_from_contracted_hours(
                self.data, candidate_solution["y"]
            ),
        }

        hard_variables = {
            "below_minimum_demand": {
                (c, t): 0
                for c in self.data["competencies"]
                for t in self.data["time"]["periods"][0][c]
            },
            "above_maximum_demand": {
                (c, t): 0
                for c in self.data["competencies"]
                for t in self.data["time"]["periods"][0][c]
            },
            "more_than_one_shift_per_day": {
                (e, i): 0
                for e in self.data["staff"]["employees"]
                for i in self.data["time"]["days"]
            },
            "cover_multiple_demand_periods": {
                (e, t): 0
                for e in self.data["staff"]["employees"]
                for j in self.data["time"]["weeks"]
                for t in self.data["time"]["combined_time_periods"][1][j]
            },
            "weekly_off_shift_error": {
                (e, j): 0
                for e in self.data["staff"]["employees"]
                for j in self.data["time"]["weeks"]
            },
            "mapping_shift_to_demand": {
                (c, t): 0
                for c in self.data["competencies"]
                for t in self.data["time"]["periods"][0]
            },
            "daily_rest_error": {
                (e, i): 0
                for e in self.data["staff"]["employees"]
                for i in self.data["time"]["days"]},

            "delta_positive_contracted_hours": {e: 0 for e in self.data["staff"]["employees"]},
        }

        objective_function, f = calculate_objective_function(
            self.data, soft_variables, candidate_solution["w"]
        )

        state = State(candidate_solution, soft_variables, hard_variables, objective_function, f)

        self.alns = ALNS(state, self.data, self.criterion)

    def get_candidate_solution(self):
        """ Generates a candidate solution for ALNS """

        self.run_esp()
        converter = Converter(self.esp)

        return converter.get_converted_variables()

    def run_esp(self):
        """ Runs ESP, with an optional presolve with SDP """

        logger.info(f"Running ESP in mode {self.mode} with {len(self.data['shifts']['shifts'])}")
        self.esp.run_model()

        return self

    def set_esp(self):
        """ Creates an appropriate Gurobi model for ESP and saves it"""

        name = f"{self.mode}_model"
        model = self.create_model(name)

        if self.mode == 0 or self.mode == "construction":
            self.esp = ConstructionModel(model, data=self.data)
            # Update configuration to get a solution as fast as possible
            self.configure_model(mip_focus=1, solution_limit=1)

        elif self.mode == 1 or self.mode == "feasibility":
            self.esp = FeasibilityModel(model, data=self.data)
            # todo: add same config as ConstructionModel?

        elif self.mode == 2 or self.mode == "optimality":
            self.esp = OptimalityModel(model, data=self.data)

        else:
            raise ValueError(f"The model choice '{self.mode}' is not valid.")

    def run_sdp(self):
        """ Runs the Shift Design Model to optimize the shift generation and saves the result """

        original_shifts = self.data["shifts"]["shifts"]
        logger.info(f"Running SDP with {len(original_shifts)} shifts")

        self.sdp.run_model()

        used_shifts = self.sdp.get_used_shifts()
        self.data["shifts"] = shift_generation.get_updated_shift_sets(
            self.problem, self.data, used_shifts
        )
        self.data["off_shifts"] = shift_generation.get_updated_off_shift_sets(
            self.data, used_shifts
        )

        percentage_reduction = (len(original_shifts) - len(used_shifts)) / len(original_shifts)
        logger.warning(
            f"SDP-reduction from {len(original_shifts)} to {len(used_shifts)} shifts "
            f"(-{100 * percentage_reduction:.2f}%)."
        )

    def set_sdp(self):
        """ Creates an appropriate Gurobi model for SDP and saves it """

        model = self.create_model(name="sdp")
        self.sdp = ShiftDesignModel(model, data=self.data)

    def configure_model(self, model="esp", **kwargs):
        """
        Dynamically configure the ESP-model by running:
            python main.py configure_model --param1=value1 --param2=value2
        """

        gurobi_model = self.esp.model if model == "esp" else self.sdp.model

        for key, value in kwargs.items():
            gurobi_model.setParam(key, value)

        return self

    def create_model(self, name):
        """ Creates a Gurobi model with standard config """

        model = Model(name=name)
        model.setParam("MIPFocus", self.mip_focus)
        model.setParam("SolutionLimit", self.solution_limit)
        model.setParam("LogToConsole", self.log_to_console)

        return model

    def __str__(self):
        """ Necessary for playing nicely with terminal usage """

        esp_value = self.esp.get_objective_value()
        message = f"ESP found solution:  {esp_value:.2f}."

        if self.alns:
            alns_value = self.alns.get_best_solution_value()
            diff = (alns_value - esp_value) / esp_value
            message += f"\nALNS found solution: {alns_value}.\nDiff {diff:.2f}%"

        return message


if __name__ == "__main__":
    """ 
    Run any function with arguments ARGS by using:
        python main.py FUNCTION_NAME ARGS
        
    Run functions in a chain:
        python main.py INIT_ARGS FUNC1 --FUNC1_ARG=FUNC1_VALUE - FUNC2 --FUNC2_ARG=FUNC2_VALUE
        
        Note: only functions that return `self` can be chained.
        Note2: functions has to be separated by `-`
    
    Access property PROP by using: 
        python main.py FUNCTION_NAME PROP
    
    Examples
        # Initialize object with default arguments and 
        python main.py
        
        # Initialize object and print self.mode
        python main.py mode
        
        # Run ESP with SDP
        python main.py run_esp
        python main.py --with_sdp run_esp
        
        # Run ESP without SDP
        python main.py --nowith_sdp run_esp
        python main.py --with_sdp=False run_esp
        
        # Configure ESP-model and then run
        python main.py configure_model --seed=1 - run_esp
        
        # Run ALNS without SDP
        python main.py --nowith_sdp run_alns
        
        # Change to SA-criterion and the run ALNS
        python main.py change_criterion --start_temp=150 - run_alns
         
    """

    fire.Fire(ProblemRunner)
