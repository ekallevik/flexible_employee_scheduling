import fire
from loguru import logger
import skopt

from main import ProblemRunner


class ParameterTuner:

    def __init__(self, problem="rproblem2"):

        self.pr = ProblemRunner(problem)

    def evaluate_parameters(self, search_params):

        decay = search_params[0]
        operator_weights = {
            "IS_REJECTED": search_params[1],
            "IS_ACCEPTED": search_params[2],
            "IS_BETTER": search_params[3],
            "IS_BEST": search_params[4],
        }
        hard_penalty = search_params[5]

        self.pr.set_alns(decay, hard_penalty, operator_weights)
        self.pr.run_alns(runtime=10)

        score = self.pr.alns.get_best_solution_value()

        return score

    def objective_func(self, params):
        """ Convert to minimization objective """
        return -1.0 * self.evaluate_parameters(params)

    def tune_hyperparameters(self):

        SPACE = [
            skopt.space.Real(0.01, 0.99, name='decay', prior='uniform'),
            skopt.space.Real(0.5, 1.0, name='is_rejected', prior='uniform'),
            skopt.space.Real(1.0, 1.3, name='is_accepted', prior='uniform'),
            skopt.space.Real(1.2, 1.5, name='is_better', prior='uniform'),
            skopt.space.Real(1.4, 1.8, name='is_best', prior='uniform'),
            skopt.space.Integer(1, 25, name='hard_penalties'),
        ]

        results = skopt.forest_minimize(self.objective_func, SPACE, n_calls=50, n_random_starts=15)
        best_result = -1.0 * results.fun
        best_params = results.x

        logger.warning(f"Best result: {best_result}")
        logger.warning(f"Best parameters: {best_params}")
        logger.warning(f"Result: {results}")

        return self


if __name__ == "__main__":

    fire.Fire(ParameterTuner)
