import json
from bisect import bisect_right, bisect_left
from math import inf

import matplotlib.pyplot as plt
from loguru import logger

files = {
    "problem1": "results/variance_3_representative/2020-06-06_20:01:09-rproblem1_mode=feasibility_sdp_reduce-seed=200.json",
    "problem2": "results/variance_3_representative/2020-06-06_20:01:20-rproblem2_mode=feasibility_sdp_reduce-seed=500.json",
    "problem3": "results/variance_3_representative/2020-06-06_20:01:26-rproblem3_mode=feasibility_sdp_reduce-seed=900.json",
    "problem4": "results/variance_3_representative/2020-06-06_20:04:24-rproblem4_mode=feasibility_sdp_reduce-seed=600.json",
    "problem5": "results/variance_3_representative/2020-06-06_20:01:36-rproblem5_mode=feasibility_sdp_reduce-seed=100.json",
    "problem6": "results/variance_3_representative/2020-06-06_20:01:41-rproblem6_mode=feasibility_sdp_reduce-seed=0.json",
    "problem7": "results/variance_3_representative/2020-06-06_20:01:50-rproblem7_mode=feasibility_sdp_reduce-seed=200.json",
    #"problem8": "results/2020-06-01_22:28:08-rproblem8_mode=feasibility_sdp_reduce.json",
    "problem9": "results/variance_3_representative/2020-06-06_20:02:10-rproblem9_mode=feasibility_sdp_reduce-seed=300.json",
}

workers = [f"worker-{j}" for j in range(48)]

def plot_best(step=1):

    for problem, file in files.items():

        with open(file) as f:
            data = json.load(f)

        construction_runtime = data["_time"]["runtime_construction"]

        worker_times = [i for i in range(step, 901-construction_runtime, step)]
        times = [i for i in range(900)]
        best_list = [-inf for _ in range(step, construction_runtime, step)]

        for time in worker_times:
            best = -inf

            for worker in workers:
                try:
                    index = bisect_left(data[worker]["objective_history"]["time"], time)

                    if index == 0:
                        continue

                    if data[worker]["objective_history"]["best"][index-1] > best:
                        best = data[worker]["objective_history"]["best"][index - 1]
                except KeyError:
                    logger.info(f"{worker} does not exist in {problem}")

            best_list.append(best)

        result = {
            "times": times,
            "best_list": best_list
                  }

        with open(f"results/{problem}-best_list.json", "w") as fp:
            json.dump(result, fp, sort_keys=True, indent=4)

        plt.plot(worker_times, best_list, "g-", markersize=6)
        plt.title(problem)
        plt.show()

def plot_history():

    for problem, file in files.items():

        with open(file) as f:
          data = json.load(f)

        for worker in workers:
            try:
                x = data[worker]["objective_history"]["time"]
                y = data[worker]["objective_history"]["best"]
                plt.plot(x, y, "o", markersize=6)
            except KeyError:
                logger.info(f"{worker} does not exist")

        plt.title(problem)
        plt.show()


plot_best(1)
