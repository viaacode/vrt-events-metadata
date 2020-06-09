import os


def load_xml_resource(eventname):
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )

    fixture_content = open(os.path.join(__location__, f"{eventname}.xml"), "rb").read()
    return fixture_content
