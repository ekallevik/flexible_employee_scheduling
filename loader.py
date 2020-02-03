import xmlschema

BASE_DIR = "../flexible_employee_scheduling_data"


def load_xml_into_dict(real_mode=False, instance=1):
    """ Loads data from the given filename """

    xsd_schema = xmlschema.XMLSchema(
        f"{BASE_DIR}/xsd schema/CreateScheduleRequest.xsd")

    if real_mode:
        xml_filepath = f"{BASE_DIR}/xml samples/Real Instances/rproblem{instance}.xml"
    else:
        xml_filepath = f"{BASE_DIR}/xml samples/Artifical Test Instances/problem{instance}.xml"

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


def get_employees(data):

    return data["SchedulePeriod"]["ScheduleRows"]



def get_data():

    data = load_xml_into_dict()

    schedule = get_schedule_info(data)