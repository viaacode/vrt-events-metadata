import os
import json


def load_xml_resource(eventname):
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )

    fixture_content = open(os.path.join(__location__, f"{eventname}.xml"), "rb").read()
    return fixture_content


def load_json_resource(filename):
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )

    content = open(os.path.join(__location__, f"{filename}.json"), "r").read()
    json_object = json.loads(content)
    return json_object
