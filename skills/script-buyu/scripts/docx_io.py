"""Bounded, read-only OOXML access; never resolve links or extract ZIP files."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree as ET

from story_contract import ContractError, require

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_BYTES = 20 * 1024 * 1024
MAX_EXPANDED = 100 * 1024 * 1024


def package(source):
    if isinstance(source, BytesIO):
        raw = source.getvalue()
    else:
        path = Path(source)
        require(path.stat().st_size <= MAX_BYTES, "DOCX exceeds 20 MiB; split or inspect separately")
        raw = path.read_bytes()
    require(len(raw) <= MAX_BYTES, "DOCX exceeds 20 MiB")
    try:
        with ZipFile(BytesIO(raw)) as archive:
            members = archive.infolist()
            require(len(members) <= 2000, "too many ZIP members")
            require(sum(item.file_size for item in members) <= MAX_EXPANDED, "expanded DOCX exceeds 100 MiB")
            names = [item.filename for item in members]
            require(len(names) == len(set(names)), "duplicate ZIP member")
            require("word/document.xml" in names, "not a Word DOCX")
            parts = {}
            for item in members:
                if item.filename.endswith((".xml", ".rels")):
                    data = archive.read(item)
                    # Reject both UTF-8 and UTF-16 declaration spellings.
                    check = data.replace(b"\x00", b"").upper()
                    require(b"<!DOCTYPE" not in check and b"<!ENTITY" not in check, "DTD or entity declaration is unsupported")
                    parts[item.filename] = ET.fromstring(data)
            require(not any("vbaProject" in name for name in names), "macro-bearing document is unsupported")
    except (BadZipFile, ET.ParseError, RuntimeError) as exc:
        raise ContractError("invalid or encrypted DOCX package") from exc
    return raw, parts


def visible_text(element):
    """Preserve visible text, tabs and soft breaks including hyperlink text."""
    result = []
    for node in element.iter():
        if node.tag in (W + "t", W + "delText"):
            result.append(node.text or "")
        elif node.tag == W + "tab":
            result.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            result.append("\n")
    return "".join(result)
