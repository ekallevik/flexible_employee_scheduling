import json
from pprint import pprint

import pandas as pd

def convert(filename):


    with open(f"{filename}.json") as f:
        data = json.load(f)

    threads = 64

    workers = [f"worker-{i}" for i in range(threads)]

    best = {}
    time = {}

    for worker in workers:
        try:
            best[worker] = data[worker]["objective_history"]["best"]
            time[worker] = data[worker]["objective_history"]["time"]
        except:
            print(f"Missing {worker} in file: {filename}")

    df_best = pd.DataFrame.from_dict(best, orient='index')
    df_time = pd.DataFrame.from_dict(time, orient='index')
    df_best.transpose()
    df_time.transpose()

    with pd.ExcelWriter(f"{filename}.xlsx") as writer:
        df_best.to_excel(writer, sheet_name='best')
        df_time.to_excel(writer, sheet_name='time')


def convert_multiple():

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
        convert(filename)


if __name__ == "__main__":
    convert_multiple()
