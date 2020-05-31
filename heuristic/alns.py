import multiprocessing
import time

import numpy as np
from functools import partial
from timeit import default_timer as timer
from heuristic.delta_calculations import *
from heuristic.destroy_operators import (
    worst_employee_removal,
    worst_week_removal,
    random_week_removal,
    weighted_random_week_removal,
    random_employee_removal, random_weekend_removal, weighted_random_employee_removal,
    worst_contract_removal,
)
from heuristic.local_search_operators import illegal_week_swap, illegal_contracted_hours

from heuristic.repair_operators import worst_week_regret_repair, worst_week_repair, \
    worst_employee_repair, worst_employee_regret_repair, week_demand_repair, \
    week_demand_per_shift_repair, week_demand_based_repair_random, week_demand_based_repair_greedy, \
    mip_week_operator_2, repair_week_based_on_f_values, mip_week_operator_3
from visualisation.barchart_plotter import BarchartPlotter


class ALNS(multiprocessing.Process):
    def __init__(self, state, criterion, data, objective_weights, log_name, decay=0.5,
                 operator_weights=None, runtime=15, worker_name=None, seed=0, results=None,
                 queue=None, share_times=None, start_time=None):

        super().__init__()
        self.queue = queue
        self.share_times = share_times
        self.worker_name = worker_name
        self.prefix = f"{self.worker_name}: " if self.worker_name else ""

        self.objective_weights = objective_weights
        self.decay = decay
        self.log_name = log_name
        self.runtime = runtime
        self.start_time = start_time

        self.initial_solution = state
        self.current_solution = state
        # current global best and feasible solution
        self.best_solution = state

        self.criterion = criterion
        self.seed = seed
        self.random_state = self.initialize_random_state(self.seed)

        self.destroy_operators = {}
        self.destroy_weights = {}
        self.repair_operators = defaultdict(dict)
        self.repair_weights = {}

        if operator_weights:
            self.WeightUpdate = operator_weights
        else:
            self.WeightUpdate = {
                "IS_BEST": 1.50,
                "IS_BETTER": 1.06,
                "IS_ACCEPTED": 1.03,
                "IS_REJECTED": 0.97
            }

        # Sets
        self.t_covered_by_off_shift = data["off_shifts"]["t_in_off_shifts"]

        self.combined_time_periods_in_week = data["time"]["combined_time_periods"][1]
        self.employee_with_competency_combination = data["staff"]["employee_with_competency_combination"]

        self.competencies = data["competencies"]
        self.demand = data["demand"]
        self.demand_per_shift = data.get("demand_per_shift", None)

        self.days = data["time"]["days"]
        self.weeks = data["time"]["weeks"]
        self.saturdays = data["time"]["saturdays"]
        self.time_step = data["time"]["step"]
        self.time_periods = data["time"]["periods"][0]
        self.time_periods_in_week = data["time"]["periods"][1]
        self.time_periods_in_day = data["time"]["periods"][2]
        self.shifts = data["shifts"]["shifts"]

        self.employees = data["staff"]["employees"]
        self.employee_with_competencies = data["staff"]["employees_with_competencies"]
        self.contracted_hours = data["staff"]["employee_contracted_hours"]

        self.shifts_at_day = data["shifts"]["shifts_per_day"]
        self.shifts_per_week = data["shifts"]["shifts_per_week"]
        self.off_shifts = data["off_shifts"]["off_shifts"]
        self.off_shift_in_week = data["off_shifts"]["off_shifts_per_week"]
        self.t_covered_by_shift = data["heuristic"]["t_covered_by_shift"]
        self.t_covered_by_off_shift = data["off_shifts"]["t_in_off_shifts"]
        self.shifts_overlapping_t = data["shifts"]["shifts_overlapping_t"]
        self.L_C_D = data["limit_on_consecutive_days"]

        self.preferences = data["preferences"]

        # Set for daily rest restriction
        self.invalid_shifts = data["shifts"]["invalid_shifts"]
        self.shift_combinations_violating_daily_rest = data["shifts"]["shift_combinations_violating_daily_rest"]
        self.shift_sequences_violating_daily_rest = data["shifts"]["shift_sequences_violating_daily_rest"]

        # Plotting and statistics
        self.results = results
        self.violation_plotter = None
        self.objective_plotter = None
        self.weight_plotter = None
        self.objective_history = {"candidate": [], "current": [], "best": [], "time": []}
        self.weight_history = defaultdict(list)
        self.iteration = 0

        self.sundays = data["time"]["sundays"]
        self.shift_lookup = data["heuristic"]["shift_lookup"]
        self.shifts_covered_by_off_shift = data["shifts"]["shifts_covered_by_off_shift"]

        get_shift_combinations(self.shift_combinations_violating_daily_rest, self.employees)

        remove_worst_week = partial(
            worst_week_removal,
            self.competencies,
            self.time_periods_in_week,
            self.combined_time_periods_in_week,
            self.employees,
            self.weeks,
            self.L_C_D,
            self.shifts_per_week,
            self.t_covered_by_shift,
        )

        remove_random_week = partial(
            random_week_removal,
            self.competencies,
            self.employees,
            self.weeks,
            self.shifts_per_week,
            self.t_covered_by_shift,
            self.random_state,
        )

        remove_weighted_random_week = partial(
            weighted_random_week_removal,
            self.competencies,
            self.time_periods_in_week,
            self.combined_time_periods_in_week,
            self.employees,
            self.weeks,
            self.L_C_D,
            self.shifts_per_week,
            self.t_covered_by_shift,
            self.random_state,
        )

        remove_random_weekend = partial(
            random_weekend_removal,
            self.competencies,
            self.employees,
            self.weeks,
            self.shifts_at_day,
            self.t_covered_by_shift,
            self.random_state,
        )

        remove_worst_employee = partial(
            worst_employee_removal,
            self.shifts,
            self.t_covered_by_shift,
            self.competencies,
        )

        remove_worst_contract = partial(
            worst_contract_removal,
            self.shifts,
            self.t_covered_by_shift,
            self.competencies,
            self.weeks,
            self.employees
        )

        remove_random_employee = partial(
            random_employee_removal,
            self.shifts,
            self.t_covered_by_shift,
            self.competencies,
            self.employees,
            self.random_state,
        )

        remove_weighted_random_employee = partial(
            weighted_random_employee_removal,
            self.shifts,
            self.t_covered_by_shift,
            self.competencies,
            self.employees,
            self.random_state,
        )

        repair_week_demand_per_shift = partial(
            week_demand_per_shift_repair,
            self.shifts_per_week,
            self.competencies,
            self.t_covered_by_shift,
            self.demand,
            self.demand_per_shift,
            self.employees,
            self.contracted_hours,
            self.shifts_at_day,
            self.time_step,
            self.time_periods_in_week,
            self.employee_with_competencies,
        )

        repair_week_demand = partial(
            week_demand_repair,
            self.shifts_per_week,
            self.competencies,
            self.t_covered_by_shift,
            self.demand,
            self.employees,
            self.contracted_hours,
            self.shifts_at_day,
            self.time_step,
            self.time_periods_in_week,
            self.employee_with_competencies,
        )

        repair_worst_week_regret = partial(
            worst_week_regret_repair,
            self.shifts_per_week,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.employee_with_competency_combination,
            self.demand,
            self.time_step,
            self.time_periods_in_week,
            self.combined_time_periods_in_week,
            self.employees,
            self.contracted_hours,
            self.invalid_shifts,
            self.shift_combinations_violating_daily_rest,
            self.shift_sequences_violating_daily_rest,
            self.weeks,
            self.shifts_at_day,
            self.L_C_D,
            self.shifts_overlapping_t,
            self.preferences
        )

        repair_worst_week_greedy = partial(
            worst_week_repair,
            self.shifts_per_week,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.employee_with_competency_combination,
            self.demand,
            self.time_step,
            self.time_periods_in_week,
            self.employees,
            self.contracted_hours,
            self.weeks,
            self.shifts_at_day,
        )

        repair_worst_employee_regret = partial(
            worst_employee_regret_repair,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.employee_with_competency_combination,
            self.demand,
            self.shifts,
            self.off_shifts,
            self.saturdays,
            self.days,
            self.L_C_D,
            self.weeks,
            self.shifts_at_day,
            self.shifts_per_week,
            self.contracted_hours,
            self.invalid_shifts,
            self.shift_combinations_violating_daily_rest,
            self.shift_sequences_violating_daily_rest,
            self.time_periods_in_week,
            self.time_step,
            self.shifts_overlapping_t,
            self.preferences
        )

        repair_worst_employee_greedy = partial(
            worst_employee_repair,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.employee_with_competency_combination,
            self.demand,
            self.contracted_hours,
            self.weeks,
            self.time_periods_in_week,
            self.time_step,
            self.shifts,
            self.shifts_at_day,
        )

        repair_worst_week_demand_based_random = partial(
            week_demand_based_repair_random,
            self.shifts_per_week, 
            self.competencies, 
            self.t_covered_by_shift,
            self.employee_with_competencies, 
            self.employee_with_competency_combination,
            self.demand,
            self.time_step,
            self.time_periods_in_week,
            self.combined_time_periods_in_week,
            self.employees, 
            self.contracted_hours, 
            self.demand_per_shift, 
            self.invalid_shifts, 
            self.shift_combinations_violating_daily_rest,
            self.shift_sequences_violating_daily_rest,
            self.weeks, 
            self.shifts_at_day,
            self.L_C_D, 
            self.shifts_overlapping_t,
            self.preferences
        )

        repair_worst_week_demand_based_greedy = partial(
            week_demand_based_repair_greedy,
            self.shifts_per_week, 
            self.competencies, 
            self.t_covered_by_shift,
            self.employee_with_competencies, 
            self.employee_with_competency_combination,
            self.demand,
            self.time_step,
            self.time_periods_in_week,
            self.combined_time_periods_in_week,
            self.employees, 
            self.contracted_hours, 
            self.demand_per_shift, 
            self.invalid_shifts, 
            self.shift_combinations_violating_daily_rest,
            self.shift_sequences_violating_daily_rest,
            self.weeks, 
            self.shifts_at_day,
            self.L_C_D, 
            self.shifts_overlapping_t,
            self.preferences
        )

        mip_operator_week_repair_2 = partial(
            mip_week_operator_2,
            self.employees, 
            self.shifts_per_week, 
            self.competencies, 
            self.time_periods_in_week, 
            self.combined_time_periods_in_week, 
            self.employee_with_competencies, 
            self.shifts_at_day, 
            self.shifts_overlapping_t, 
            self.t_covered_by_off_shift,
            self.invalid_shifts, 
            self.shift_combinations_violating_daily_rest, 
            self.shift_sequences_violating_daily_rest,
            self.weeks, 
            self.time_step, 
            self.demand, 
            self.days,
            self.objective_weights,
            self.contracted_hours,
            self.t_covered_by_shift,
            self.L_C_D, 
            self.preferences
        )

        mip_operator_week_repair_3 = partial(
            mip_week_operator_3,
            self.employees, 
            self.shifts_per_week, 
            self.competencies, 
            self.time_periods_in_week, 
            self.combined_time_periods_in_week, 
            self.employee_with_competencies, 
            self.shifts_at_day, 
            self.shifts_overlapping_t, 
            self.t_covered_by_off_shift,
            self.invalid_shifts, 
            self.shift_combinations_violating_daily_rest, 
            self.shift_sequences_violating_daily_rest,
            self.weeks, 
            self.time_step, 
            self.demand, 
            self.days,
            self.objective_weights,
            self.contracted_hours,
            self.t_covered_by_shift,
            self.demand_per_shift,
            self.L_C_D,
            self.preferences
        )

        repair_worst_week_f_value = partial(
            repair_week_based_on_f_values,
            self.shifts_per_week,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.employee_with_competency_combination,
            self.demand,
            self.time_step,
            self.time_periods_in_week,
            self.combined_time_periods_in_week,
            self.employees,
            self.contracted_hours,
            self.invalid_shifts,
            self.shift_combinations_violating_daily_rest,
            self.shift_sequences_violating_daily_rest,
            self.weeks,
            self.shifts_at_day,
            self.L_C_D,
            self.shifts_overlapping_t,
            self.objective_weights, 
            self.preferences, 
            self.demand_per_shift,
            self.saturdays,
            self.days
        )
        
        operators = {
            remove_worst_employee: [
                 repair_worst_employee_regret,
                 #repair_worst_employee_greedy
            ],

            remove_worst_contract: [
                repair_worst_employee_regret,
                #repair_worst_employee_greedy
            ],

            remove_random_employee: [
                repair_worst_employee_regret,
                #repair_worst_employee_greedy
            ],

            remove_weighted_random_employee: [
                repair_worst_employee_regret,
                #repair_worst_employee_greedy
            ],

            remove_worst_week: [
                repair_worst_week_regret,
                repair_worst_week_greedy,
                repair_week_demand,
                repair_week_demand_per_shift,
                repair_worst_week_demand_based_random,
                repair_worst_week_demand_based_greedy,
                mip_operator_week_repair_2,
                repair_worst_week_f_value,
                mip_operator_week_repair_3
            ],

            remove_random_week: [
                repair_worst_week_regret,
                repair_worst_week_greedy,
                repair_week_demand,
                repair_week_demand_per_shift,
                repair_worst_week_demand_based_random,
                repair_worst_week_demand_based_greedy,
                mip_operator_week_repair_2,
                repair_worst_week_f_value,
                mip_operator_week_repair_3
            ],

            remove_weighted_random_week: [
                repair_worst_week_regret,
                repair_worst_week_greedy,
                repair_week_demand,
                repair_week_demand_per_shift,
                repair_worst_week_demand_based_random,
                repair_worst_week_demand_based_greedy,
                mip_operator_week_repair_2,
                repair_worst_week_f_value,
                mip_operator_week_repair_3
            ],

            remove_random_weekend: [
                repair_worst_week_regret,
                repair_worst_week_greedy
            ],
        }

        self.add_destroy_and_repair_operators(operators)
        self.initialize_destroy_and_repair_weights()

    def run(self):
        """ Automatically called when multiprocess.start() is run """

        self.iterate(runtime=self.runtime)

        # self.save_solutions()

        results = {
            "log": self.log_name,
            "worker": self.worker_name,
            "best_solution": self.get_best_solution_value(),
            "iterations": self.iteration,
            "destroy_weights": self.destroy_weights,
            "repair_weights": self.repair_weights,
            "decay": self.decay,
            "criterion:": str(self.criterion),
            "weight_update": self.WeightUpdate,
            "random_seed": self.seed,
            "random_state": str(self.random_state),
            "objective_history": self.objective_history
        }

        self.results[self.worker_name] = results
        logger.warning(f"{self.prefix}Saved results")
        self.close_queue()

    def close_queue(self):

        logger.info(f"{self.prefix}Cooling off before closing queue")
        time.sleep(15)

        logger.info(f"{self.prefix}Closing queue")
        while True:
            logger.trace(f"{self.prefix}Trying to flush queue")
            if self.queue.empty():
                logger.warning(f"{self.prefix}Queue is empty")
                self.queue.put(None)
                break
            shared_solution = self.queue.get()
            if shared_solution is None:
                # Poison pill means shutdown
                logger.warning(f"{self.prefix}Shared solution is None and Queue is empty")
                self.queue.put(None)
                break

        self.queue.close()
        logger.trace(f"{self.prefix}Queue closed")

        self.queue.join_thread()
        logger.trace(f"{self.prefix}Join thread")

    def iterate(self, iterations=None, runtime=None):
        """ Performs iterations until runtime is reached or the number of iterations is exceeded """

        runtime_in_seconds = runtime * 60 if runtime else None

        if not iterations:
            logger.warning(f"{self.prefix}Running ALNS for {runtime} minutes")

            while timer() < self.start_time + runtime_in_seconds:
                try:
                    self.perform_iteration()
                except KeyboardInterrupt:
                    command = input("\n\nAvailable commands: \n"
                                    "1 - Continue running \n"
                                    "2 - Save solutions and continue running \n"
                                    "3 - Drop into debugger \n"
                                    "4 - Save solutions and stop running\n"
                                    )

                    if command == "1":
                        continue
                    elif command == "2":
                        custom_filename = input("\nEnter custom filename or hit enter to use "
                                                "log_name\n")

                        custom_filename = custom_filename if len(custom_filename) else None
                        self.save_solutions(custom_filename)

                        continue

                    elif command == "3":
                        breakpoint()
                    elif command == "4":
                        break

        else:

            logger.warning(f"Running ALNS for {iterations} iterations")

            for iteration in range(iterations):
                self.perform_iteration()

        # Add a newline after the output from the last iteration
        print()
        logger.warning(f"{self.prefix}Performed {iterations if iterations else self.iteration} iterations over"
                       f" {timer() - self.start_time:.2f}s (including construction)")

        logger.error(f"{self.prefix}Initial solution: {self.initial_solution.get_objective_value(): .2f}")
        logger.error(f"{self.prefix}Best solution: {self.best_solution.get_objective_value(): .2f}")


    def perform_iteration(self):

        # Add a newline between the output of each iteration
        print()
        current_time = timer()-self.start_time
        logger.warning(f"{self.prefix}Iteration: {self.iteration} at {current_time}")

        if self.share_times and current_time > self.share_times[0]:
            self.share_solutions()

        candidate_solution = self.current_solution.copy()
        destroy_operator, destroy_operator_id = self.select_operator(self.destroy_operators, self.destroy_weights)
        repair_operator, repair_operator_id = self.select_operator(self.repair_operators[destroy_operator_id], self.repair_weights[destroy_operator_id])

        destroy_set, destroy_specific_set = destroy_operator(candidate_solution)
        repair_set = repair_operator(candidate_solution, destroy_set, destroy_specific_set)

        self.calculate_objective(candidate_solution, destroy_set, repair_set)
        self.consider_candidate_and_update_weights(candidate_solution, destroy_operator_id, repair_operator_id)

        if self.violation_plotter:
            violations = candidate_solution.get_violations_per_week(
                self.weeks, self.time_periods_in_week, self.competencies, self.employees
            )

            self.violation_plotter.plot_data(violations)

        self.update_objective_history(candidate_solution, current_time)

        if self.objective_plotter:
            self.objective_plotter.plot_data(self.objective_history)

        if self.weight_plotter:

            for key, value in self.destroy_weights.items():
                self.weight_history[key].append(value)
                self.weight_plotter.plot_data(self.weight_history)

        self.iteration += 1

        return candidate_solution

    def share_solutions(self):

        logger.error(f"{self.prefix}Sharing at {self.share_times[0]}s."
                     f" {len(self.share_times) - 1} shares remaining")
        del self.share_times[0]

        if not self.queue.empty():
            shared_solution = self.queue.get()
            logger.error(f"{self.prefix}Shared solution={shared_solution.get_objective_value(): 7.2f} vs "
                         f"best={self.get_best_solution_value(): 7.2f}")

            if self.criterion.accept(shared_solution, self.current_solution,
                                     self.best_solution, self.random_state):
                self.current_solution = shared_solution
                logger.error(f"{self.prefix}Shared solution is accepted")

                if shared_solution.get_objective_value() >= self.best_solution.get_objective_value():
                    self.best_solution = shared_solution
                    logger.error(f"{self.prefix}Shared solution is best solution")
            else:
                logger.error(f"{self.prefix}Shared solution is rejected")

        self.queue.put(self.best_solution)

    def update_objective_history(self, candidate_solution, current_time):

        self.objective_history["candidate"].append(candidate_solution.get_objective_value())
        self.objective_history["current"].append(self.current_solution.get_objective_value())
        self.objective_history["best"].append(self.best_solution.get_objective_value())
        self.objective_history["time"].append(current_time)

    def consider_candidate_and_update_weights(self, candidate_solution, destroy_id, repair_id):
        """
        Considers the candidate based on self.critertion, and will update the weights
        :param candidate_solution: The solution to consider
        :param destroy_id: the id (name) of the destroy function used to create this state
        :param repair_id: the id (name) of the repair function used to create this state
        """
        logger.warning(f"{self.current_solution.get_objective_value(): 7.2f}  vs "
                       f"{candidate_solution.get_objective_value(): 7.2f} "
                       f"({destroy_id}, {repair_id})")

        self.choose_local_search(candidate_solution)

        if self.criterion.accept(candidate_solution, self.current_solution,
                                 self.best_solution, self.random_state):
            self.current_solution = candidate_solution

            if candidate_solution.get_objective_value() >= self.current_solution.get_objective_value():
                logger.debug("Candidate is better")
                weight_update = self.WeightUpdate["IS_BETTER"]
            else:
                weight_update = self.WeightUpdate["IS_ACCEPTED"]
                logger.info("Candidate is accepted")

        else:
            logger.trace("Candidate is rejected")
            weight_update = self.WeightUpdate["IS_REJECTED"]

        # only feasible solution can be considered for best solution
        if (candidate_solution.is_feasible()
                and candidate_solution.get_objective_value() >
                self.best_solution.get_objective_value()):
            logger.critical(f"Candidate is best")
            weight_update = self.WeightUpdate["IS_BEST"]
            self.best_solution = candidate_solution
            self.current_solution = candidate_solution

        self.update_weights(weight_update, destroy_id, repair_id)

    def save_solutions(self, custom_name=None):

        if custom_name:
            filename = custom_name
        else:
            filename = self.log_name

        suffix = f"-{self.worker_name}" if self.worker_name else ""
        self.best_solution.write(f"solutions/{filename}-ALNS{suffix}")

    def select_operator(self, operators, weights):
        """
        Randomly selects an operator from a probability distribution based on the operators weights.
        :param operators: self.destroy_operators or self.repair_operators
        :param weights: the weights associated with the operators
        :return: the operator function, and it´s ID.
        """

        probabilities = self.get_probabilities(weights)

        message = f"Probabilities for " \
                  f"{'Destroy' if 'worst_week_removal' in operators.keys() else 'Repair'} ["

        for p in probabilities:
            message += f" {p*100:.1f}%"

        message += " ]"
        logger.trace(message)

        selected_operator_id = self.random_state.choice(list(operators.keys()), p=probabilities)
        return operators[selected_operator_id], selected_operator_id

    @staticmethod
    def get_probabilities(weights):
        total_weight = sum(weights.values())
        return [weight / total_weight for weight in weights.values()]

    def update_weights(self, weight_update, destroy_id, repair_id):
        """ Updates the value of the operator pair by multiplying both with weight_update """

        self.destroy_weights[destroy_id] = (
                self.decay * self.destroy_weights[destroy_id] + (1-self.decay) * weight_update
        )

        self.repair_weights[destroy_id][repair_id] = (
                self.decay * self.repair_weights[destroy_id][repair_id] + (1-self.decay) * weight_update
        )

    def initialize_destroy_and_repair_weights(self):
        self.destroy_weights = self.initialize_weights(self.destroy_operators)
        for destroy_operator in self.destroy_operators:
            self.repair_weights[destroy_operator] = self.initialize_weights(self.repair_operators[destroy_operator])

    @staticmethod
    def initialize_weights(operators):
        if not operators:
            raise ValueError("You cannot initialize weights before adding at least one operator")

        return {operator: 1.0 for operator in operators}

    @staticmethod
    def initialize_random_state(seed):
        """ Provides a seeded random state to ensure a deterministic output over different runs """
        return np.random.RandomState(seed)

    def add_destroy_and_repair_operators(self, operators):

        for destroy_operator, repair_operator_set in operators.items():

            self.destroy_operators[destroy_operator.func.__name__] = destroy_operator
            self.add_repair_operator(destroy_operator.func.__name__, operators[destroy_operator])

    def add_repair_operator(self, destroy_operator_id, repair_operators):
        for new_operator in repair_operators:
            self.repair_operators[destroy_operator_id][new_operator.func.__name__] = new_operator

    def calculate_objective(self, state, destroy, repair):
        destroy_repair_set = destroy + repair
        employees = set([e for e, t, v in destroy_repair_set])

        # Updates the current states soft variables based on changed decision variables
        calculate_deviation_from_demand(
            state,
            self.competencies,
            self.t_covered_by_shift,
            self.employee_with_competencies,
            self.demand,
            destroy_repair_set,
        )

        delta_calculate_negative_deviation_from_contracted_hours(
            state,
            employees,
            self.contracted_hours,
            self.weeks,
            self.time_periods_in_week,
            self.competencies,
            self.time_step,
        )

        calculate_partial_weekends(state, employees, self.shifts_at_day, self.saturdays)
        calculate_isolated_working_days(state, employees, self.shifts_at_day, self.days)
        calculate_isolated_off_days(state, employees, self.shifts_at_day, self.days)
        calculate_consecutive_days(state, employees, self.shifts_at_day, self.L_C_D, self.days)
        calculate_weekly_rest(state, self.shifts_per_week, employees, self.weeks)
        calculate_daily_rest_error(state, [destroy, repair], self.invalid_shifts, self.shift_combinations_violating_daily_rest, self.shift_sequences_violating_daily_rest)
        
        # Updates the current states hard variables based on changed decision variables
        below_minimum_demand(state, destroy_repair_set, self.employee_with_competencies, self.demand, self.competencies, self.t_covered_by_shift)
        above_maximum_demand(state, destroy_repair_set, self.employee_with_competencies, self.demand, self.competencies, self.t_covered_by_shift)
        more_than_one_shift_per_day(state, employees, self.demand, self.shifts_at_day, self.days)
        cover_multiple_demand_periods(state, repair, self.t_covered_by_shift, self.competencies)
        mapping_shift_to_demand(
            state,
            destroy_repair_set,
            self.t_covered_by_shift,
            self.shifts_overlapping_t,
            self.competencies,
        )

        return calculate_objective_function(
            state,
            employees,
            self.saturdays,
            self.L_C_D,
            self.days,
            self.weeks,
            self.objective_weights,
            self.preferences,
            self.competencies
        )

    def get_best_solution_value(self):
        return self.best_solution.get_objective_value()

    def choose_local_search(self, candidate_solution):
        penalties = {
            "below_minimum_demand": sum(candidate_solution.hard_vars["below_minimum_demand"].values()),
            "above_maximum_demand": sum(candidate_solution.hard_vars["above_maximum_demand"].values()),
            "negative_contracted_hours": sum(candidate_solution.hard_vars["delta_positive_contracted_hours"].values()),
            "weekly_off_shift_error": sum(candidate_solution.hard_vars["weekly_off_shift_error"].values())
        }

        current_value = self.current_solution.get_objective_value()

        if 0 < current_value/candidate_solution.get_objective_value() < 2:
            if (not penalties["below_minimum_demand"] or not penalties["below_minimum_demand"]) and penalties["weekly_off_shift_error"]:

                    destroy_set, repair_set = illegal_week_swap(
                        self.shifts_per_week,
                        self.employees,
                        self.shifts_at_day,
                        self.t_covered_by_shift,
                        self.competencies,
                        self.contracted_hours,
                        self.invalid_shifts, 
                        self.shift_combinations_violating_daily_rest, 
                        self.shift_sequences_violating_daily_rest,
                        self.time_periods_in_week,
                        self.time_step,
                        self.L_C_D,
                        self.preferences,
                        self.weeks,
                        self.combined_time_periods_in_week,
                        candidate_solution,
                    )

                    destroy, repair = illegal_contracted_hours(candidate_solution, self.shifts, self.time_step, self.employees, self.shifts_at_day, self.weeks, self.t_covered_by_shift, self.contracted_hours, self.time_periods_in_week, self.competencies)

                    self.calculate_objective(candidate_solution, destroy_set + destroy, repair_set + repair)

                    updated_value = self.current_solution.get_objective_value()
                    logger.trace(f"week_swap and contracted_hours increased value from "
                                 f"{current_value} to {updated_value}")


            elif penalties["negative_contracted_hours"] and not (penalties["below_minimum_demand"] or penalties["below_minimum_demand"]):

                    destroy_set, repair_set = illegal_contracted_hours(candidate_solution, self.shifts, self.time_step, self.employees, self.shifts_at_day, self.weeks, self.t_covered_by_shift, self.contracted_hours, self.time_periods_in_week, self.competencies)

                    self.calculate_objective(candidate_solution, destroy_set, repair_set)

                    updated_value = self.current_solution.get_objective_value()
                    logger.trace(f"week_swap and contracted_hours increased value from "
                                 f"{current_value} to {updated_value}")

