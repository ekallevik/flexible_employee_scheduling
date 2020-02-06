import math

import xmlschema

from constants import HOURS_IN_A_DAY

BASE_DIR = "../flexible_employee_scheduling_data"


def load_xml_into_dict(real_mode=False, instance=1):
    """ Loads data from the given filename """

    xsd_schema = xmlschema.XMLSchema(
        f"{BASE_DIR}/xsd schema/CreateScheduleRequest.xsd")

    if real_mode:
        xml_filepath = f"{BASE_DIR}/xml samples/Real Instances/rproblem{instance}.xml"
    else:
        xml_filepath = f"{BASE_DIR}/xml samples/Artificial Test Instances/problem{instance}.xml"

    # Validates an instances against the definition, and converts to dict
    if xsd_schema.is_valid(xml_filepath):
        return xsd_schema.to_dict(xml_filepath)
    else:
        raise ValueError("XML file not valid")


def get_schedule_info(data):
    """ Returns the schedule information from XML data in a nicely formatted dict """

    return {
        "number_of_weeks": data["ScheduleInfo"]["NbrOfWeeks"],
    }


def get_employee_info(data):

    employee_list = data["SchedulePeriod"]["ScheduleRows"]["ScheduleRow"]

    number_of_employees = len(employee_list)
    working_hours = []
    competencies = {}

    for employee_id, employee in enumerate(employee_list):
        working_hours.append(employee["WeekHours"])

        for competency in employee["Competences"]["CompetenceId"]:
            if competency in competencies:
                competencies[competency].append(employee_id)
            else:
                competencies[competency] = [employee_id]

    return number_of_employees, working_hours, competencies


def adjust_times(time, round_up=True, time_step=1):

    if time[1] % time_step > 0:
        factor = math.ceil(time[1] / time_step) if round_up else math.floor(time[1] / time_step)
        time = [time[0], factor * time_step]
        if time[1] == 60:
            time = [time[0] + 1, 0]

    return time


def format_task(task, time_step):

    time_start = [int(x) for x in str.split(task['TimeStart'], ":")]
    time_end = [int(x) for x in str.split(task['TimeEnd'], ":")]

    task["TimeStart"] = adjust_times(time_start, round_up=True, time_step=time_step)
    task["TimeEnd"] = adjust_times(time_end, round_up=False, time_step=time_step)

    return task


def format_demand_definitions(demand_definitions, time_step=1):

    formatted_definitions = {}

    for definition in demand_definitions:
        day_demand_id = definition["DayDemandId"]
        tasks = []
        for task in definition["Rows"]["Row"]:
            tasks.append(format_task(task, time_step))
        formatted_definitions[day_demand_id] = tasks

    return formatted_definitions


def convert_task_times_to_range(task, time_step):

    return range(1, 2)



def aggregate_definitions(demand_definitions, time_step=1):

    formatted_definitions = format_demand_definitions(demand_definitions, time_step=time_step)

    day_size = int(HOURS_IN_A_DAY/time_step)
    day_array = [0 for t in range(day_size)]
    aggregated_definitions = [day_array for i in formatted_definitions]

    for day_demand_id, day_demand in formatted_definitions.items():
        print(day_demand)
        for task in day_demand:
            print(task)

            for t in convert_task_times_to_range(task, time_step):
                aggregated_definitions[day_demand_id][t] += task["Min"]

    return aggregated_definitions




def get_tasks(demand_definitions):

    tasks = {}

    for definition in demand_definitions:
        demand_id = definition["DayDemandId"]

        tasks[demand_id] = [task for task in definition["Rows"]["Row"]]

    return tasks


def aggregate_demand(data):

    demand = {}
    tasks = get_tasks(data["Demands"]["DemandDefinitions"]["DemandDefinition"])

    for day_demand_id in tasks:
        print(tasks[day_demand_id])

    return demand


def get_data():

    data = load_xml_into_dict()

    schedule = get_schedule_info(data)
