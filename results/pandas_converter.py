import pandas as pd

filename = "2020-05-29_19:07:54-rproblem1_mode=feasibility_sdp_reduce"

df = pd.read_json(f"{filename}.json")

with pd.ExcelWriter(f"{filename}.xlsx") as writer:
    df.to_excel(writer)