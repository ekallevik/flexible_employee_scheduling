import json
from bisect import bisect_left
from math import inf

import matplotlib.pyplot as plt
from loguru import logger

files = {
    "problem1": "results/variance_3_representative/2020-06-06_20:01:09-rproblem1_mode=feasibility_sdp_reduce-seed=200",
    "problem2": "results/variance_3_representative/2020-06-06_20:01:20-rproblem2_mode=feasibility_sdp_reduce-seed=500",
    "problem3": "results/variance_3_representative/2020-06-06_20:01:26-rproblem3_mode=feasibility_sdp_reduce-seed=900",
    "problem4": "results/variance_3_representative/2020-06-06_20:04:24-rproblem4_mode=feasibility_sdp_reduce-seed=300",
    "problem5": "results/variance_3_representative/2020-06-06_20:01:36-rproblem5_mode=feasibility_sdp_reduce-seed=100",
    "problem6": "results/variance_3_representative/2020-06-06_20:01:41-rproblem6_mode=feasibility_sdp_reduce-seed=0",
    "problem7": "results/variance_3_representative/2020-06-06_20:01:50-rproblem7_mode=feasibility_sdp_reduce-seed=200",
    #"problem8": "results/2020-06-01_22:28:08-rproblem8_mode=feasibility_sdp_reduce.json",
    "problem9": "results/variance_3_representative/2020-06-06_20:02:10-rproblem9_mode=feasibility_sdp_reduce-seed=300",
}

files_plns = {
    "problem1": "results/plns/2020-06-05_19:49:46-rproblem1_mode=feasibility_sdp_reduce-plns",
    "problem2": "results/plns/2020-06-05_19:49:53-rproblem2_mode=feasibility_sdp_reduce-plns",
    "problem3": "results/plns/2020-06-05_19:50:09-rproblem3_mode=feasibility_sdp_reduce-plns",
    #"problem4": "",
    "problem5": "results/plns/2020-06-05_19:50:23-rproblem5_mode=feasibility_sdp_reduce-plns",
    "problem6": "results/plns/2020-06-05_19:50:30-rproblem6_mode=feasibility_sdp_reduce-plns",
    "problem7": "results/plns/2020-06-05_19:50:50-rproblem7_mode=feasibility_sdp_reduce-plns",
    "problem8": "results/plns/2020-06-05_19:50:59-rproblem8_mode=feasibility_sdp_reduce-plns",
    "problem9": "results/plns/2020-06-05_19:55:58-rproblem9_mode=feasibility_sdp_reduce-plns",
}



optimal_value = {
    "problem1": 2588.96,
    "problem2": 1990.05,
    "problem3": 6517.02,
    "problem4": 2158.56,
    "problem5": 3514.83,
    "problem6": 3889.74,
    "problem7": 6502.45,
    "problem8": 1000.95,
    "problem9": 6764.54,
}

workers = [f"worker-{j}" for j in range(48)]

def plot_best(step=1, mode="gap", foldername="variance"):

    if foldername=="plns":
        folder = files_plns
    else:
        folder = files

    for problem, filename in folder.items():

        with open(f"{filename}.json") as f:
            data = json.load(f)

        construction_runtime = int(data["_time"]["runtime_construction"]) + 1

        worker_times = [i for i in range(step, 900-construction_runtime, step)]
        times = [i for i in range(901)]
        best_list = [-inf for _ in range(step, construction_runtime, step)]
        gap_list = [-inf for _ in range(step, construction_runtime, step)]
        opt_value = optimal_value[problem]

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
            gap = 100*abs(opt_value-best)/abs(best)
            gap_list.append(gap)

        diff = len(times) - len(best_list)
        for _ in range(diff):
            best_list.append(best_list[-1])
            gap_list.append(gap_list[-1])

        result = {
            "times": times,
            "best_list": best_list,
            "gap_li"
            "st": gap_list
                  }

        with open(f"{filename}-best.json", "w") as fp:
            json.dump(result, fp, sort_keys=True, indent=4)

        y_values = gap_list if mode == "gap" else best_list

        if mode == "gap":
            plt.ylim(0, 25)

        plt.plot(times, y_values, markersize=6, label=problem)
    plt.xticks([i for i in range(0, 901, 100)])
    plt.yticks([i for i in range(0, 26, 5)], [f"{i}%" for i in range(0, 26, 5)])
    plt.grid(b=True, which='major', axis='both', color='gainsboro', linestyle='-', linewidth=0.5)
    plt.legend()
    plt.title("Gap as a function of runtime")
    plt.savefig("palns_gap")

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
