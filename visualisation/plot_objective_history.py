import json
from bisect import bisect_right, bisect_left
from math import inf

import matplotlib.pyplot as plt
from loguru import logger

files = {
    "problem1": "results/2020-06-01_21:56:38-rproblem1_mode=feasibility_sdp_reduce.json",
    "problem2": "results/2020-06-01_21:56:58-rproblem2_mode=feasibility_sdp_reduce.json",
    "problem3": "results/2020-06-01_20:12:30-rproblem3_mode=feasibility_sdp_reduce.json",
    "problem4": "results/2020-05-31_16:48:29-rproblem4_mode=feasibility_sdp_reduce.json",
    "problem5": "results/2020-06-01_21:56:50-rproblem5_mode=feasibility_sdp_reduce.json",
    "problem6": "results/2020-06-01_21:30:29-rproblem6_mode=feasibility_sdp_reduce.json",
    "problem7": "results/2020-06-01_21:30:32-rproblem7_mode=feasibility_sdp_reduce.json",
    "problem8": "results/2020-06-01_22:28:08-rproblem8_mode=feasibility_sdp_reduce.json",
    "problem9": "results/2020-06-01_21:30:41-rproblem9_mode=feasibility_sdp_reduce.json",
}

workers = [f"worker-{j}" for j in range(40)]

def plot_best(step=5):

    for problem, file in files.items():

        times = [i for i in range(step, 900, step)]
        best_list = []

        with open(file) as f:
            data = json.load(f)

        for time in times:
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

        #plt.plot(times, best_list, "g-", markersize=6)
        #plt.title(problem)
        #plt.show()

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
