import json
from statistics import stdev, mean

import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats


def plot_distribution(filename):

    with open(f"{filename}.json") as f:
        data = json.load(f)

    threads = 64
    workers = [f"worker-{i}" for i in range(threads)]

    solutions = []
    iterations = []

    for worker in workers:
        try:
            solutions.append(data[worker]["best_solution"])
            iterations.append(data[worker]["iterations"])
        except:
            print(f"Missing {worker} in file: {filename}")

    sns.set(color_codes=True)
    dist_plot = sns.distplot(solutions)
    #plt.suptitle(f"Distribution plot for 64 different seeds")
    plt.suptitle(filename)

    mean_solution = mean(solutions)
    stddev_solution = stdev(solutions)
    mean_iterations = mean(iterations)

    plt.title(f"avg: {mean_solution:.2f}, Stddev: {stddev_solution:.2f}, avg iter="
              f"{mean_iterations:.2f}")
    plt.show()

    fig = dist_plot.get_figure()
    fig.savefig(f"{filename}.png")


def plot_multiple():

    filenames = [
        "2020-05-29_19:07:54-rproblem1_mode=feasibility_sdp_reduce",
        "2020-05-29_19:07:59-rproblem2_mode=feasibility_sdp_reduce",
        "2020-05-29_19:08:09-rproblem3_mode=feasibility_sdp_reduce",
        "2020-05-29_19:08:15-rproblem4_mode=feasibility_sdp_reduce",
        "2020-05-29_19:23:35-rproblem5_mode=feasibility_sdp_reduce",
        "2020-05-29_19:23:54-rproblem6_mode=feasibility_sdp_reduce",
        "2020-05-29_19:24:03-rproblem7_mode=feasibility_sdp_reduce",
        "2020-05-29_19:24:06-rproblem8_mode=feasibility_sdp_reduce",
        "2020-05-29_19:39:41-rproblem9_mode=feasibility_sdp_reduce",
    ]

    for filename in filenames:
        plot_distribution(filename)


if __name__ == "__main__":
    plot_multiple()


