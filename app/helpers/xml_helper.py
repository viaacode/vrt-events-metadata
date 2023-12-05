from lxml import etree
from pathlib import Path


def transform_to_ebucore(xml: str) -> bytes:
    xslt_path = Path.cwd() / "app" / "resources" / "ebucore.xslt"
    xslt = etree.parse(str(xslt_path.resolve()))

    transform = etree.XSLT(xslt)

    return etree.tostring(
        transform(etree.fromstring(xml)),
        pretty_print=True,
        encoding="UTF-8",
        xml_declaration=True,
    )


def construct_sidecar(metadata: dict) -> bytes:
    pid = metadata["PID"]
    media_id = metadata["MEDIA_ID"]
    root = etree.Element("MediaHAVEN_external_metadata")
    etree.SubElement(root, "title").text = f"Collateral: pid: {pid}"

    description = f"""Metadata for essence:
    - PID: {pid}
    - Media ID: {media_id}
    - CP: VRT
    """
    etree.SubElement(root, "description").text = description

    mdprops = etree.SubElement(root, "MDProperties")
    etree.SubElement(mdprops, "CP").text = "VRT"
    etree.SubElement(mdprops, "CP_id").text = "OR-rf5kf25"
    etree.SubElement(mdprops, "sp_name").text = "s3"
    etree.SubElement(mdprops, "PID").text = f"{pid}_metadata"
    etree.SubElement(mdprops, "md5").text = metadata["Md5"]
    # Add VRT "Media ID" as local_id
    etree.SubElement(mdprops, "dc_identifier_localid").text = media_id
    # Add VRT "Media ID" as itself under local_ids
    local_ids = etree.SubElement(mdprops, "dc_identifier_localids")
    etree.SubElement(local_ids, "MEDIA_ID").text = media_id

    relations = etree.SubElement(mdprops, "dc_relations")
    etree.SubElement(relations, "is_verwant_aan").text = pid
    # Information for deewee
    etree.SubElement(mdprops, "object_level").text = "file"
    etree.SubElement(mdprops, "object_use").text = "metadata"
    etree.SubElement(mdprops, "ie_type").text = "n/a"
    tree = etree.ElementTree(root)
    return etree.tostring(
        root, pretty_print=True, encoding="UTF-8", xml_declaration=True
    )


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
