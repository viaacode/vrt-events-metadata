from lxml import etree
from pathlib import Path
import io


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


def construct_sidecar(metadata: dict) -> str:
    pid = metadata["PID"]
    root = etree.Element("MediaHAVEN_external_metadata")
    etree.SubElement(root, "title").text = f"Collateral: pid: {pid}"

    description = f"""Metadata for essence:
    - PID: {pid}
    - CP: VRT
    """
    etree.SubElement(root, "description").text = description

    mdprops = etree.SubElement(root, "MDProperties")
    etree.SubElement(mdprops, "CP").text = "VRT"
    etree.SubElement(mdprops, "CP_id").text = "OR-rf5kf25"
    etree.SubElement(mdprops, "sp_name").text = "s3"
    etree.SubElement(mdprops, "PID").text = f"{pid}_metadata"
    etree.SubElement(mdprops, "md5").text = metadata["Md5"]

    relations = etree.SubElement(mdprops, "dc_relations")
    etree.SubElement(relations, "is_verwant_aan").text = pid
    tree = etree.ElementTree(root)
    return etree.tostring(
        root, pretty_print=True, encoding="UTF-8", xml_declaration=True
    )
