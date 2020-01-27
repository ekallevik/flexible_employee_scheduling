

def load_xml_into_dict(filename):
    """ Loads data from the given filename """


    xsd_schema = xmlschema.XMLSchema('data/xsd schema/CreateScheduleRequest.xsd')

    if "rproblem" in filename:
        xml_filepath = f'data/xml samples/Real Instances/{filename}.xml'
    else:
        xml_filepath = f'data/xml samples/Artifical Test Instances/{filename}.xml'

    # Validates an instances against the definition, and converts to dict
    if xsd_schema.is_valid(xml_filepath):
        return xsd_schema.to_dict(xml_filepath)
    else:
        raise ValueError("XML file not valid")