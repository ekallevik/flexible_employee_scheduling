import re
import plotly.figure_factory as ff
from datetime import datetime, timedelta, time as dt, date
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import sys
from pathlib import Path

#Paths
data_folder = Path(__file__).resolve().parents[2] / 'flexible_employee_scheduling_data/xml data/Real Instances/'
solution_folder = Path(__file__).resolve().parents[1]
loader_path = Path(__file__).resolve().parents[1] 
loader_path = loader_path / 'xml_loader'
sys.path.insert(1, str(loader_path))
from xml_loader import *

# creating indices
key_y = re.compile('\d*,\d*,\d*')
key_x = re.compile('\d*,\d+\.?\d*,\d*\.?\d*')
key_w = re.compile('\d*,\d*.?\d*,\d*.?\d*')


today = datetime.combine(date.today(), dt(0,0,0))

def visualize_demand(min_demand, ideal_demand, max_demand, number_of_days):
    """
    Plots a bar chart to visualize the demand. If the chart is only one color it means that minimum demand
    equals maximum demand.

    :param min_demand:
    :param ideal_demand:
    :param max_demand:
    :param number_of_days
    """

    for day in range(number_of_days):
        fix, ax = plt.subplots()

        start_time = day * HOURS_IN_A_DAY
        end_time = start_time + HOURS_IN_A_DAY - 1

        # Sets multiple plot, with the last initialization foremost.
        max_plot = ax.bar(range(HOURS_IN_A_DAY - 1), max_demand[start_time:end_time])
        ideal_plot = ax.bar(range(HOURS_IN_A_DAY - 1), ideal_demand[start_time:end_time])
        min_plot = ax.bar(range(HOURS_IN_A_DAY - 1), min_demand[start_time:end_time])

        plt.title(f'Demand for day={day}')
        plt.legend(["Maximum demand", "Ideal demand", "Minimum demand"])
        plt.ylabel('Number of employees')
        plt.xlabel("Time periods")

        # Setting appropriate tick values
        plt.xticks(range(HOURS_IN_A_DAY))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

        plt.savefig(f'figures/Demand for day={day}')


def create_gantt_chart(data, solution):
    #days = periods * 7
    df = []
    for day in data:
        for i in range(len(data[day].start)):
            demand_start_time = datetime.combine(day, data[day].start[i])
            demand_finish_time = datetime.combine(day, data[day].end[i])
            dictionary = dict(Task="Demand",
                          Start=demand_start_time,
                          Finish=demand_finish_time,
                          Resource="Demand_" + str(data[day].ideal[i]))
            df.append(dictionary)

    # for ele in data:
    #     demand_start_time = date + timedelta(hours=ele[0])
    #     demand_finish_time = date + timedelta(hours=ele[0] + 1)
    #     dictionary = dict(Task="Demand",
    #                       Start=demand_start_time,
    #                       Finish=demand_finish_time,
    #                       Resource="Demand_" + str(ele[1]))
    #     df.append(dictionary)

    with open(solution) as file:
        line = file.readline()

        while line:
            if not (line.rstrip().endswith('0')):
                # if line.startswith('y'):
                #     k = key_y.findall(line)[0].split(',')

                if line.startswith('x'):
                    k = key_x.findall(line)[0].split(',')
                    if(float(k[1]) - int(float(k[1])) != 0):
                        minute = 60/(1/(float(k[1]) - int(float(k[1]))))
                    else:
                        minute = 0
                    start_time = today + timedelta(hours=int(float(k[1])), minutes=minute)

                    end = float(k[1]) + float(k[2])

                    if(end - int(end) != 0):
                        minute = 60/(1/(end - int(end)))
                    else:
                        minute = 0

                    finish_time = today + timedelta(hours=int(end), minutes= minute)
                    dictionary = dict(Task="Employee " + str(int(k[0])),
                                      Start=start_time,
                                      Finish=finish_time,
                                      Resource="Work")
                    df.append(dictionary)

                if line.startswith('w'):
                    k = key_w.findall(line)[0].split(',')
                    print(k)
                    if(float(k[1]) - int(float(k[1])) != 0):
                        minute = 60/(1/(float(k[1]) - int(float(k[1]))))
                    else:
                        minute = 0
                    start_time = today + timedelta(hours=int(float(k[1])), minutes=minute)

                    end = float(k[1]) + float(k[2])

                    if(end - int(end) != 0):
                        minute = 60/(1/(end - int(end)))
                    else:
                        minute = 0

                    finish_time = today + timedelta(hours=int(end), minutes= minute)



                    dictionary = dict(Task="Employee " + str(int(k[0])),
                                      Start=start_time,
                                      Finish=finish_time,
                                      Resource="Off")
                    df.append(dictionary)
            line = file.readline()

# 247, 249, 248
#  239, 244, 242
#  231, 239, 236
#  223, 234, 230
#  215, 229, 224
#  207, 224, 217
#  199, 219, 211
#  191, 214, 205
#  183, 209, 199
# Demand_10='175, 204, 193'
#  Demand_11='168, 199, 187'
#  Demand_12='153, 181, 170'
#  Demand_13='138, 163, 154'
#  Demand_14='123, 145, 137'
#  Demand_15='107, 127, 119'
#  Demand_16='92, 109, 102'
#  Demand_17='77, 91, 85'
#  Demand_18='62, 73, 68'
#  Demand_19='46, 55, 51'
#  Demand_20='31, 37, 34'
#  Demand_21='16, 19, 17'


    colors = dict(Work='rgb(46, 137, 205)', Off='rgb(198, 47, 105)',
                  Demand_1='rgb(247, 249, 248)', Demand_2='rgb(239, 244, 242)', Demand_3='rgb(231, 239, 236)',
                  Demand_4='rgb(223, 234, 230)', Demand_5='rgb(215, 229, 224)', Demand_6='rgb(207, 224, 217)', Demand_7='rgb(199, 219, 211)',
                  Demand_8='rgb(191, 214, 205)', Demand_9='rgb(183, 209, 199)', Demand_10='rgb(175, 204, 193)', Demand_11='rgb(168, 199, 187)', 
                  Demand_12='rgb(153, 181, 170)', Demand_13='rgb(138, 163, 154)', Demand_14='rgb(123, 145, 137)', Demand_15='rgb(107, 127, 119)',
                  Demand_16='rgb(92, 109, 102)', Demand_17='rgb(77, 91, 85)', Demand_18='rgb(62, 73, 68)', Demand_19='rgb(46, 55, 51)', Demand_20='rgb(31, 37, 34)',
                  Demand_21='rgb(16, 19, 17)', Demand_22='rgb(0, 19, 17)' , Demand_23='rgb(16, 50, 18)' , Demand_24= 'rgb(50, 50, 17)', Demand_25= 'rgb(70, 70, 17)',
                  Demand_26= 'rgb(16, 80, 80)', Demand_27= 'rgb(16, 90, 90)', Demand_28='rgb(16, 200, 120)', Demand_29='rgb(210, 190, 210)',
                  Demand_30='rgb(100, 100, 100)', Demand_31='rgb(120, 120, 120)', Demand_32='rgb(140, 140, 140)', Demand_33='rgb(160, 160, 160)')

    fig = ff.create_gantt(df, colors=colors, index_col='Resource', show_colorbar=True, group_tasks=True)
    print("Not Done")
    fig.show()


def main():
    demand = get_days_with_demand2()
    # case = "base_v3.4.json"
    solution = str(solution_folder / "test_4.sol")
    
    

    create_gantt_chart(demand, solution)


if __name__ == '__main__':
    main()
