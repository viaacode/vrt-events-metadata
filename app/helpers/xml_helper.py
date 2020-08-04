from lxml import etree
from pathlib import Path
import io


def transform_to_ebucore(xml: str) -> bytes:
    xslt_path = Path.cwd() / "app" / "resources" / "ebucore.xslt"
    xslt = etree.parse(str(xslt_path.resolve()))

    transform = etree.XSLT(xslt)
    return etree.tostring(transform(etree.parse(io.StringIO(xml))))
