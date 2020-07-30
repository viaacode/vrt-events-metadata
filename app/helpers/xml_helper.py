from lxml import etree
from pathlib import Path


def transform_to_ebucore(xml):
    xslt_path = Path.cwd() / "app" / "resources" / "ebucore.xslt"
    xslt = etree.parse(str(xslt_path.resolve()))

    transform = etree.XSLT(xslt)
    return etree.tostring(transform(xml))
