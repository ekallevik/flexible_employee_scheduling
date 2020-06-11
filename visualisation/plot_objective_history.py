import json
from bisect import bisect_left
from math import inf

import matplotlib.pyplot as plt
from loguru import logger

colors = {
    "problem1": "b",
    "problem2": "y",
    "problem3": "g",
    "problem4": "r",
    "problem5": "m",
    "problem6": "saddlebrown",
    "problem7": "c",
    "problem8": "hotpink",
    "problem9": "navy",
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

linestyles = ["solid", "dashdot", "dashed", "dotted", (0, (5, 10)), (0, (1, 10))]

def load_data(filename):
    with open(f"{filename}.json") as f:
        data = json.load(f)
    return data


class ProblemPlotter:

    def __init__(self, problem, variants, title, plot, step=1):
        self.problem = problem
        self.title = title
        self.variants = variants
        self.step = step
        self.color = colors[problem]

        self.construction_runtime = None
        self.worker_times = None
        self.times = None
        self.opt_value = optimal_value[problem]

        self.get_shared_stats()
        self.plot_variants()

        self.plot = plot
        self.setup_matplotlib()

    def setup_matplotlib(self):
        self.plot.ylim(0, 25)
        self.plot.xticks([i for i in range(0, 901, 100)])
        self.plot.yticks([i for i in range(0, 26, 5)], [f"{i}%" for i in range(0, 26, 5)])
        self.plot.grid(b=True, which='major', axis='both', color='gainsboro', linestyle='-',
                       linewidth=0.5)
        self.plot.legend()
        self.plot.suptitle("Gap as a function of runtime")
        self.plot.title(self.title)

    def show(self):
        self.plot.show()

    def save(self):
        self.plot.savefig(f"{self.title}_gap")

    def get_shared_stats(self):
        filename = files[self.problem]

        data = load_data(filename)

        self.construction_runtime = int(data["_time"]["runtime_construction"]) + 1

        self.worker_times = [i for i in range(self.step, 900 - self.construction_runtime,
                                              self.step)]
        self.times = [i for i in range(901)]

    def plot_variants(self):

        for counter, (name, filename) in enumerate(self.variants.items()):

            best_list, gap_list = self.get_variant_data_as_list(filename)
            self.pad_data_lists(best_list, gap_list)

            plt.plot(self.times, gap_list, markersize=6, label=f"{self.problem}-{name}",
                     color=self.color, linestyle=linestyles[counter])

    def pad_data_lists(self, best_list, gap_list):
        diff = len(self.times) - len(best_list)
        for _ in range(diff):
            gap_list.append(gap_list[-1])

    def get_variant_data_as_list(self, variant):
        data = load_data(variant)

        best_list = [-inf for _ in range(self.step, self.construction_runtime, self.step)]
        gap_list = [-inf for _ in range(self.step, self.construction_runtime, self.step)]

        for time in self.worker_times:
            best = -inf

            for worker in workers:
                try:
                    index = bisect_left(data[worker]["objective_history"]["time"], time)
                    if index == 0:
                        continue
                    if data[worker]["objective_history"]["best"][index - 1] > best:
                        best = data[worker]["objective_history"]["best"][index - 1]
                except KeyError:
                    logger.info(f"{worker} does not exist in {self.problem}")

            best_list.append(best)
            gap = 100 * abs(self.opt_value - best) / abs(best)
            gap_list.append(gap)
        return best_list, gap_list


def plot_best(step=1, mode="gap", foldername="variance"):

    if foldername=="plns":
        folder_list = [files, files_plns]
    elif foldername =="share":
        folder_list = [files_share_9]
    else:
        folder_list = files

    for folder in folder_list:
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

            linestyle = "-" if folder == files else "--"
            plt.plot(times, y_values, markersize=6, label=problem, color=colors["problem9"],
                     linestyle=linestyle)

    plt.xticks([i for i in range(0, 901, 100)])
    plt.yticks([i for i in range(0, 26, 5)], [f"{i}%" for i in range(0, 26, 5)])
    plt.grid(b=True, which='major', axis='both', color='gainsboro', linestyle='-', linewidth=0.5)
    plt.legend()
    plt.suptitle("Gap as a function of runtime")
    plt.title(foldername)
    plt.savefig(f"{foldername}_gap")
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


files_share_3 = {
    "na": "results/share_times/2020-06-08_22:43:43-rproblem3_mode=feasibility_sdp_reduce-share=None_seed=400",
    "5s": "results/share_times/2020-06-08_17:31:06-rproblem3_mode=feasibility_sdp_reduce-share=5s_seed=100",
    "10s": "results/variance_3_representative/2020-06-06_20:01:26-rproblem3_mode=feasibility_sdp_reduce-seed=900",
    "20s": "results/share_times/2020-06-08_17:31:06-rproblem3_mode=feasibility_sdp_reduce-share=20s_seed=0",
}

files_share_5 = {
    "na": "results/share_times/2020-06-08_22:45:17-rproblem5_mode=feasibility_sdp_reduce-share=None_seed=100",
    "5s": "results/share_times/2020-06-08_17:31:11-rproblem5_mode=feasibility_sdp_reduce-share=5s_seed=100",
    "10s": "results/variance_3_representative/2020-06-06_20:01:36-rproblem5_mode=feasibility_sdp_reduce-seed=100",
    "20s": "results/share_times/2020-06-08_17:31:11-rproblem5_mode=feasibility_sdp_reduce-share=20s_seed=400",
}

files_share_6 = {
    "na": "results/share_times/2020-06-08_23:50:17-rproblem6_mode=feasibility_sdp_reduce-share=None_seed=400",
    "5s": "results/share_times/2020-06-08_23:50:17-rproblem6_mode=feasibility_sdp_reduce-share=5s_seed=0",
    "10s": "results/variance_3_representative/2020-06-06_20:01:41-rproblem6_mode=feasibility_sdp_reduce-seed=0",
    "20s": "results/share_times/2020-06-08_23:50:17-rproblem6_mode=feasibility_sdp_reduce-share=20s_seed=100"

}

files_share_7 = {
    "na": "results/share_times/2020-06-08_22:45:52-rproblem7_mode=feasibility_sdp_reduce-share=None_seed=300",
    "5s": "results/share_times/2020-06-08_17:31:22-rproblem7_mode=feasibility_sdp_reduce-share=5s_seed=400",
    "10s": "results/variance_3_representative/2020-06-06_20:01:50-rproblem7_mode=feasibility_sdp_reduce-seed=200",
    "20s": "results/share_times/2020-06-08_17:31:22-rproblem7_mode=feasibility_sdp_reduce-share=20s_seed=200",
}

files_share_9 = {
    "na": "results/share_times/2020-06-08_22:46:00-rproblem9_mode=feasibility_sdp_reduce-share=None_seed=0",
    "5s": "results/share_times/2020-06-08_17:31:27-rproblem9_mode=feasibility_sdp_reduce-share=5s_seed=0",
    "10s": "results/variance_3_representative/2020-06-06_20:02:10-rproblem9_mode=feasibility_sdp_reduce-seed=300",
    "20s": "results/share_times/2020-06-08_17:31:27-rproblem9_mode=feasibility_sdp_reduce-share=20s_seed=100",
}

files_threads_3 = {
    1: "results/threads/2020-06-08_17:31:47-rproblem3_mode=feasibility_sdp_reduce-threads=1_seed=0",
    4: "results/threads/2020-06-08_17:31:47-rproblem3_mode=feasibility_sdp_reduce-threads=4_seed=300",
    8: "results/threads/2020-06-08_17:31:47-rproblem3_mode=feasibility_sdp_reduce-threads=8_seed=400",
    16: "results/threads/2020-06-08_17:31:47-rproblem3_mode=feasibility_sdp_reduce-threads=16_seed=0",
    32: "results/threads/2020-06-08_17:31:47-rproblem3_mode=feasibility_sdp_reduce-threads=32_seed=300",
    48: "results/variance_3_representative/2020-06-06_20:01:26-rproblem3_mode=feasibility_sdp_reduce-seed=900",
}

files_threads_5 = {
    1: "results/threads/2020-06-08_17:31:51-rproblem5_mode=feasibility_sdp_reduce-threads=1_seed=300",
    4: "results/threads/2020-06-08_17:31:51-rproblem5_mode=feasibility_sdp_reduce-threads=4_seed=400",
    8: "results/threads/2020-06-08_17:31:51-rproblem5_mode=feasibility_sdp_reduce-threads=8_seed=200",
    16: "results/threads/2020-06-08_17:31:51-rproblem5_mode=feasibility_sdp_reduce-threads=16_seed=200",
    32: "results/threads/2020-06-08_17:31:51-rproblem5_mode=feasibility_sdp_reduce-threads=32_seed=0",
    48: "results/variance_3_representative/2020-06-06_20:01:36-rproblem5_mode=feasibility_sdp_reduce-seed=100",
}

files_threads_6 = {
    48: "results/variance_3_representative/2020-06-06_20:01:41-rproblem6_mode=feasibility_sdp_reduce-seed=0",
}

files_threads_7 = {
    1: "results/threads/2020-06-08_22:46:40-rproblem7_mode=feasibility_sdp_reduce-threads=1_seed=300",
    4: "results/threads/2020-06-08_22:46:40-rproblem7_mode=feasibility_sdp_reduce-threads=4_seed=400",
    8: "results/threads/2020-06-08_17:32:01-rproblem7_mode=feasibility_sdp_reduce-threads=8_seed=100",
    16: "results/threads/2020-06-08_17:32:01-rproblem7_mode=feasibility_sdp_reduce-threads=16_seed=200",
    32: "results/threads/2020-06-08_17:32:01-rproblem7_mode=feasibility_sdp_reduce-threads=32_seed=100",
    48: "results/variance_3_representative/2020-06-06_20:01:50-rproblem7_mode=feasibility_sdp_reduce-seed=200",
}

files_threads_9 = {
    1: "results/threads/2020-06-08_17:32:05-rproblem9_mode=feasibility_sdp_reduce-threads=1_seed=300",
    4: "results/threads/2020-06-08_17:32:05-rproblem9_mode=feasibility_sdp_reduce-threads=4_seed=100",
    8: "results/threads/2020-06-08_17:32:05-rproblem9_mode=feasibility_sdp_reduce-threads=8_seed=300",
    16: "results/threads/2020-06-08_17:32:05-rproblem9_mode=feasibility_sdp_reduce-threads=16_seed=300",
    32: "results/threads/2020-06-08_17:32:05-rproblem9_mode=feasibility_sdp_reduce-threads=32_seed=200",
    48: "results/variance_3_representative/2020-06-06_20:02:10-rproblem9_mode=feasibility_sdp_reduce-seed=300",
}


def plot_sharing():

    plot = plt
    p3 = ProblemPlotter(problem="problem3", variants=files_share_3, title="Sharing", plot=plot)
    plot.show()

    p5 = ProblemPlotter(problem="problem5", variants=files_share_5, title="Sharing", plot=plot)
    plt.show()

    p6 = ProblemPlotter(problem="problem6", variants=files_share_6, title="Sharing", plot=plot)
    plot.show()

    p7 = ProblemPlotter(problem="problem7", variants=files_share_7, title="Sharing", plot=plot)
    plot.show()

    p9 = ProblemPlotter(problem="problem9", variants=files_share_9, title="Sharing", plot=plot)
    plt.show()


def plot_threads():

    plot = plt
    p3 = ProblemPlotter(problem="problem3", variants=files_threads_3, title="Number of threads",
                        plot=plot)
    plt.show()

    p5 = ProblemPlotter(problem="problem5", variants=files_threads_5, title="Number of threads", plot=plot)
    plt.show()

    #p6 = ProblemPlotter(problem="problem6", variants=files_threads_6, title="Number of threads",
    # plot=plot)
    #plt.show()

    p7 = ProblemPlotter(problem="problem7", variants=files_threads_7, title="Number of threads", plot=plot)
    plt.show()

    p9 = ProblemPlotter(problem="problem9", variants=files_threads_9, title="Number of threads", plot=plot)
    plt.show()


def main():
    plot_sharing()


if __name__ == "__main__":
    main()
