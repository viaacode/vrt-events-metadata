from lxml import etree
from pathlib import Path
import io


def transform_to_ebucore(xml: str) -> bytes:
    xslt_path = Path.cwd() / "app" / "resources" / "ebucore.xslt"
    xslt = etree.parse(str(xslt_path.resolve()))

    transform = etree.XSLT(xslt)
    return etree.tostring(
        transform(xml), pretty_print=True, encoding="UTF-8", xml_declaration=True,
    )


def construct_sidecar(metadata: dict) -> str:
    root = etree.Element("MediaHAVEN_external_metadata")
    etree.SubElement(root, "title").text = f"Collateral: pid: {pid}"

    description = f"""Metadata for essence:
    - PID: {metadata["PID"]}
    - CP: {metadata["CP"]}
    """
    etree.SubElement(root, "description").text = description

    mdprops = etree.SubElement(root, "MDProperties")
    etree.SubElement(mdprops, "CP").text = "VRT"
    etree.SubElement(mdprops, "CP_id").text = "OR-rf5kf25"
    etree.SubElement(mdprops, "sp_name").text = "s3"
    etree.SubElement(mdprops, "PID").text = metadata["PID"]
    etree.SubElement(mdprops, "md5").text = metadata["Md5"]

    relations = etree.SubElement(root, "dc_relations")
    etree.SubElement(relations, "is_deel_van").text = metadata["PID"]
    tree = etree.ElementTree(root)
    return etree.tostring(
        root, pretty_print=True, encoding="UTF-8", xml_declaration=True
    )
