from lxml import etree
from pathlib import Path


def generate_make_subtitle_available_request_xml(
    ot_type: str, correlation_id: str, media_id: str
) -> bytes:
    NAMESPACES = {
        None: "http://www.vrt.be/mig/viaa",
    }
    xml_data_dict = {
        "requestor": "meemoo",
        "correlationId": correlation_id,
        "id": media_id,
        "destinationPath": f"mam-collaterals/{ot_type}OT/{media_id}/",
        "otType": ot_type.upper(),
    }

    root = etree.Element("makeSubtitleAvailableRequest", nsmap=NAMESPACES)
    for sub, val in xml_data_dict.items():
        etree.SubElement(root, sub).text = val
    return etree.tostring(
        root, pretty_print=True, encoding="UTF-8", xml_declaration=True
    )
