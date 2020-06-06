import json
import multiprocessing
import time
from copy import deepcopy
from datetime import datetime
from multiprocessing import Queue
import neptune


import fire
from gurobipy import *
from loguru import logger
from timeit import default_timer as timer


from heuristic.alns import ALNS
from heuristic.criterions.greedy_criterion import GreedyCriterion
from heuristic.criterions.record_to_record_travel import RecordToRecordTravel
from heuristic.heuristic_calculations import *
from heuristic.criterions.simulated_annealing_criterion import SimulatedAnnealingCriterion
from heuristic.state import State
from model.construction_model import ConstructionModel
from model.feasibility_model import FeasibilityModel
from model.optimality_model import OptimalityModel
from model.shift_design_model import ShiftDesignModel
from model.implicit_model import ImplicitModel
from preprocessing import shift_generation
from results.converter import Converter
from utils.log_formatter import LogFormatter
from utils.weights import get_weights
from visualisation.barchart_plotter import BarchartPlotter
from visualisation.heatmap_plotter import HeatmapPlotter
from visualisation.objective_plotter import ObjectivePlotter

formatter = LogFormatter()

# Increase the level to get less output
# Trace < Info < Debug < Warning < Error < Critical
level_per_module = {
    "__main__": "INFO",
    "preprocessing.xml_loader": "WARNING",
    "heuristic.alns": "CRITICAL",
    "heuristic.delta_calculations": "CRITICAL",
    "heuristic.destroy_operators": "CRITICAL",
    "heuristic.repair_operators": "CRITICAL",
    "heuristic.criterions.simulated_annealing_criterion": "CRITICAL",
}

logger.remove()
logger.add(sys.stderr, level="TRACE", format=formatter.format, filter=level_per_module)


class ProblemRunner:
    def __init__(self, problem="rproblem3", mode="feasibility", with_sdp=True, log_name=None,
                 update_shifts=True, time_limit=10000, use_predefined_shifts=False,
                 log_to_file=True, runtime=900):

        """
        Holds common data across all problems. Use --arg_name=arg_value from the terminal to
        use non-default values
        """

        logger.info(f"Setting up runner for {problem}")
        self.problem = problem
        self.mode = mode
        self.runtime = runtime
        self.start_time = None
        self.construction_runtime = None

        self.log_name = None
        self.log_to_file = log_to_file
        self.set_log_name(log_name, with_sdp, use_predefined_shifts, update_shifts)

        self.data = shift_generation.load_data(problem, use_predefined_shifts)
        self.weights = get_weights(self.data["time"], self.data["staff"])

        # Standard Gurobi-config
        self.mip_focus = "default"
        self.solution_limit = "default"
        self.log_to_console = 1
        self.time_limit = time_limit

        self.sdp = None
        if with_sdp and (self.mode != "implicit" and self.mode != 3) and not use_predefined_shifts:
            self.set_sdp()
            self.run_sdp(update_shifts)

        self.esp = None
        self.candidate_solution = None

        self.criterion = GreedyCriterion()
        self.alns = None
        self.palns_results = None

        self.set_esp()

    def set_log_name(self, log_name, with_sdp, use_predefined_shifts, update_shifts):

        if log_name:
            actual_name = log_name
        else:
            if with_sdp:
                if update_shifts:
                    shift_set = "sdp_reduce"
                else:
                    shift_set = "sdp_no_reduce"
            elif use_predefined_shifts:
                shift_set = "predefined_shifts"
            elif self.mode == "implicit" or self.mode == 3:
                shift_set = "implicit_shifts"
            else:
                shift_set = "no_sdp"

            actual_name = f"{self.problem}_mode={self.mode}_{shift_set}"

        now = datetime.now()
        self.log_name = f"{now.strftime('%Y-%m-%d_%H:%M:%S')}-{actual_name}"
        if self.log_to_file:
            logger.add(f"logs/{self.log_name}.log", format=formatter.format)
        else:
            logger.critical("Does not log to file!")

    def rerun_esp(self):
        """ Extracts the best legal solution from ALNS and uses it as a start for MIP """

        solution = self.alns.best_solution

        model = self.create_model("rerun_esp")
        esp = OptimalityModel(model, data=self.data)

        for key, value in solution.x.items():
            esp.var.x[key].start = value

        for key, value in solution.y.items():
            esp.var.y[key].start = value

        logger.warning("Rerunning model")
        esp.run_model()

        return self

    def test_seeds(self, n_runs=10, start_seed=0, threads=48):

        logger.warning(f"Running {self.problem} for {n_runs} runs")

        for seed in range(start_seed, start_seed+n_runs*100, 100):
            self.run_palns(threads=threads, seed_offset=seed, variant=f"seed={seed}")

        return self

    def test_threads(self):

        thread_list = [32, 16, 8, 4, 1]

        for threads in thread_list:
            self.run_palns(threads=threads, variant=f"threads={threads}")

        return self

    def run_palns(self, threads=48, share_freq=10, share_start=60, seed_offset=0,
                  accept="g", variant="default"):
        """ Runs multiple ALNS-instances in parallel and saves the results to a JSON-file """

        if accept == "sa":
            criterion = SimulatedAnnealingCriterion(start_temperature=1700, end_temperature=150,
                                                     step=30)
        elif accept == "rrt":
            criterion = RecordToRecordTravel(start_threshold=1700, end_threshold=150, step=30)
        else:
            criterion = GreedyCriterion()    

        logger.critical(f"Running {self.problem} with runtime {self.runtime} in {threads} threads")
        logger.warning(f"Using {criterion}")

        candidate_solution = self.get_candidate_solution()
        state = self.get_state(candidate_solution)
        initial_solution = state.get_objective_value()

        manager = multiprocessing.Manager()
        shared_results = manager.dict()
        queue = Queue()

        # the interval for which the PALNS should share data
        share_times = [i for i in range(share_start, 15*60, share_freq)]

        logger.critical(f"Running PALNS with {threads} processes with variant={variant}")

        processes = []
        for j in range(threads):
            state_copy = deepcopy(state)

            decay = 0.9
            operator_weights = {
                "IS_BEST": 10,
                "IS_BETTER": 4,
                "IS_ACCEPTED": 2,
                "IS_REJECTED": 0.7
            }

            worker_name = f"worker-{j}"

            remaining_runtime = self.runtime-self.construction_runtime

            alns = ALNS(state_copy, criterion, self.data, self.weights, self.log_name, decay=decay,
                        operator_weights=operator_weights, runtime=remaining_runtime,
                        worker_name=worker_name, results=shared_results, queue=queue, share_times=share_times,
                        seed=j+seed_offset, variant=variant)
            processes.append(alns)

            logger.info(f"Starting {worker_name}")
            alns.start()

        logger.warning("Cooling off for 30s")
        time.sleep(30)

        for process in processes:
            logger.critical(f"Terminating {process.worker_name}")
            try:
                process.queue.close()
                logger.info(f"{process.worker_name}: Queue closed")
            except Exception as e:
                logger.exception(f"{process.worker_name}: Queue not closed", e)
            try:
                process.queue.join_thread()
                logger.info(f"{process.worker_name}: Queue joined")
            except Exception as e:
                logger.exception(f"{process.worker_name}: Queue not joined", e)
                pass
            try:
                process.join()
                logger.info(f"{process.worker_name}: Process joined")
            except Exception as e:
                logger.exception(f"{process.worker_name}: Could not join thread", e)
                pass

        self.save_shared_results(shared_results, initial_solution=initial_solution,
                                 share_times=share_times, threads=threads, variant=variant, processes=processes)

        return self

    def save_shared_results(self, shared_results, initial_solution, share_times,
                            threads, variant, processes=None):

        print()
        logger.warning("Saving multiprocessing results")

        best_solution = max((result["best_solution"], worker) for worker, result in shared_results.items())
        global_best_solution = best_solution[0]
        global_best_worker = best_solution[1]
        global_iterations = sum(result["iterations"] for result in shared_results.values())
        logger.info(f"Global best solution: {global_best_solution} found by {global_best_worker}")
        logger.info(f"Global iterations: {global_iterations}")

        shared_results["_log_name"] = self.log_name
        shared_results["_problem"] = self.problem
        shared_results["_variant"] = variant
        shared_results["_solution"] = {"initial_solution": initial_solution,
                                       "global_best_solution": global_best_solution,
                                       "global_best_worker": global_best_worker,
                                       "global_iterations": global_iterations}
        shared_results["_threads"] = threads
        shared_results["_time"] = {"runtime_total": self.runtime,
                                   "time_start": self.start_time,
                                   "runtime_construction": self.construction_runtime,
                                   "time_share": share_times}

        self.palns_results = shared_results

        with open(f"results/{self.log_name}-{variant}.json", "w") as fp:
            json.dump(shared_results.copy(), fp, sort_keys=True, indent=4)
        logger.info(f"Saved PALNS results to results/{self.log_name}-{variant}.json")

    def run_alns(self, decay=0.5, iterations=None, runtime=15, plot_objective=False,
                 plot_violations_map=False, plot_violations_bar=False, plot_weights=False):
        """ Runs ALNS on the generated candidate solution """

        self.set_alns(decay=decay)

        if plot_objective + plot_violations_map + plot_violations_bar + plot_weights > 1:
            raise ValueError("Cannot use more than one plot")

        if plot_objective:
            self.alns.objective_plotter = ObjectivePlotter(title="Objective value per iteration",
                                                           log_name=self.log_name)
            self.alns.objective_plotter.set_scale("symlog")

        if plot_weights:
            self.alns.weight_plotter = ObjectivePlotter(title="Destroy weights per iteration",
                                                        log_name=self.log_name)

        if plot_violations_map:
            self.alns.violation_plotter = HeatmapPlotter(title="Violations for current iteration",
                                                         log_name=self.log_name)

        if plot_violations_bar:
            self.alns.violation_plotter = BarchartPlotter(title="Violations for current iteration",
                                                          log_name=self.log_name)
        try:
            self.alns.iterate(iterations, runtime)
        except Exception as e:
            logger.exception(f"An exception occured in {self.log_name}", exception=e,
                             diagnose=True, backtrace=True)

        return self

    def change_criterion(self, start_temp=100, end_temp=1, step=1, method="linear"):
        """ Changes the criterion to Simulated Annealing"""

        self.criterion = SimulatedAnnealingCriterion(
            method=method, start_temperature=start_temp, end_temperature=end_temp, step=step
        )

        return self

    def set_alns(self, decay, operator_weights=None):
        """ Sets ALNS based on the given config """

        candidate_solution = self.get_candidate_solution()
        state = self.get_state(candidate_solution)

        logger.info(f"ALNS with {decay} and {self.criterion}")
        self.alns = ALNS(state, self.criterion, self.data, self.weights, self.log_name, decay,
                         start_time=self.start_time)

    def get_state(self, candidate_solution):
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
            "below_minimum_demand": {},
            "above_maximum_demand": {},
            "more_than_one_shift_per_day": {},
            "cover_multiple_demand_periods": {},
            "weekly_off_shift_error": {},
            "mapping_shift_to_demand": {},
            "daily_rest_error": {},
            "delta_positive_contracted_hours": {},
        }
        objective_function, f = calculate_objective_function(self.data, soft_variables,
                                                             self.weights, candidate_solution["w"],
                                                             candidate_solution["y"])
        state = State(candidate_solution, soft_variables, hard_variables, objective_function, f)
        return state

    def get_candidate_solution(self):
        """ Generates a candidate solution for ALNS """

        if not self.candidate_solution:

            self.run_esp()
            converter = Converter(self.esp)
            self.candidate_solution = converter.get_converted_variables()

        return self.candidate_solution

    def run_esp(self):
        """ Runs ESP, with an optional presolve with SDP """

        if self.mode != "implicit" and self.mode != 3:
            logger.info(f"Running ESP in mode {self.mode} with {len(self.esp.shifts_set['shifts'])}")
        else:
            logger.info(f"Running ESP in mode {self.mode} with implicitly generated shifts")

        try:
            self.start_time = timer()
            logger.trace(f"Model run started at: {self.start_time}")
            self.esp.run_model()
        except Exception as e:
            logger.exception(f"An exception occured in {self.log_name}", exception=e,
                             diagnose=True, backtrace=True)

        if not self.construction_runtime:
            self.construction_runtime = timer() - self.start_time
            logger.warning(f"Completed construction in {self.construction_runtime:.2f}s")

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

        elif self.mode == 2 or self.mode == "optimality":
            self.esp = OptimalityModel(model, data=self.data)

        elif self.mode == 3 or self.mode == "implicit":
            self.esp = ImplicitModel(model, data=self.data)

        else:
            raise ValueError(f"The model choice '{self.mode}' is not valid.")

    def run_sdp(self, update_shifts):
        """ Runs the Shift Design Model to optimize the shift generation and saves the result """

        original_shifts = self.data["shifts"]["shifts"]
        logger.info(f"Running SDP with {len(original_shifts)} shifts")

        self.sdp.run_model()

        used_shifts, unused_shifts = self.sdp.get_used_shifts()

        self.data["demand_per_shift"] = self.sdp.get_demand_per_shift()

        if update_shifts:
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
        model.setParam("LogFile", f"gurobi_logs/{self.log_name}.log")
        model.setParam("MIPFocus", self.mip_focus)
        model.setParam("SolutionLimit", self.solution_limit)
        model.setParam("LogToConsole", self.log_to_console)
        model.setParam("TimeLimit", self.time_limit)

        return model

    def save_results(self):
        """ Saves the results from the current run """

        if self.sdp:
            self.sdp.save_solution(self.log_name)
            logger.warning(f"Saved SDP-solution to solutions/{self.log_name}-SDP.sol")

        self.esp.save_solution(self.log_name)
        logger.warning(f"Saved ESP-solution to solutions/{self.log_name}-ESP.sol")

        if self.alns:
            self.alns.save_solutions()

    def __str__(self):
        """
        Necessary for playing nicely with terminal usage. This function is called
        automagically after completion of the terminal command.
        """
        print()
        logger.info(f"Completed run for {self.log_name}")

        # Saves the results from the run
        self.save_results()

        return self.log_name

    def run_neptune(self, tags, description=None, project="ALNS"):
        """ Uploads parameters, results and logs to neptune.ai. Tags can be passed in as a list """

        self.save_results()

        logger.info("Logging to Neptune")

        params = {
            "problem": self.problem,
            "with_sdp": True if self.sdp else False,
            "esp_mode": self.mode,
            "weights": self.weights,
        }

        # NEPTUNE_API_TOKEN environment variable needs to be defined.
        neptune_project = f"ekallevik/{project}"
        logger.info(f"Logging to Neptune project: {neptune_project}")
        neptune.init(neptune_project)

        if project == "ALNS":
            #params["critertion"] = self.alns.criterion
            #params["operator_weights"] = self.alns.WeightUpdate
            #params["alns_initial_solution"] = self.alns.initial_solution.get_objective_value()
            #params["alns_best_solution"] = self.alns.best_solution.get_objective_value()
            #params["iterations"] = self.alns.iteration
            #params["random_state"] = self.alns.random_state
            params["palns_results"] = self.palns_results

        neptune.create_experiment(name=self.log_name, params=params, description=description,
                                  tags=tags)

        neptune.log_artifact(f"gurobi_logs/{self.log_name}.log")
        neptune.log_artifact(f"logs/{self.log_name}.log")
        neptune.log_artifact(f"solutions/{self.log_name}-SDP.sol")
        neptune.log_artifact(f"solutions/{self.log_name}-ESP.sol")

        try:
            logger.info("Uploading JSON results")
            neptune.log_artifact(f"{self.log_name}.json")
        except:
            logger.info("No JSON results found")
            pass

        return self


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

        #Håkons base command
        python3 main.py --with_sdp=False change_criterion --start_temp=100 - run_alns --iterations=10 
         
    """

    fire.Fire(ProblemRunner)


