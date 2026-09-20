"""Inventory a general incoming DOCX; preserve text, flag non-text for review."""
import argparse
from docx_io import package, visible_text, W
from story_contract import ContractError, write_json_new


def read_source(source):
    _, parts = package(source)
    root = parts["word/document.xml"]
    body = root.find(W + "body")
    if body is None:
        raise ContractError("missing document body")
    blocks = []
    for index, element in enumerate(body, 1):
        if element.tag == W + "sectPr":
            continue
        block = {"order": index, "type": element.tag.rsplit("}", 1)[-1]}
        if element.tag == W + "tbl":
            block["rows"] = [["\n".join(visible_text(p) for p in cell.iter(W + "p")) for cell in row.findall(W + "tc")] for row in element.findall(W + "tr")]
            allowed = {"tbl": {"tblPr", "tblGrid", "tr"}, "tr": {"trPr", "tc"}, "tc": {"tcPr", "p"}}
            unusual = any(child.tag not in {W + name for name in children} for tag, children in allowed.items() for parent in element.iter(W + tag) for child in parent)
            if unusual:
                block["structure_warning"] = "unsupported_table_structure_requires_review"
                block["unresolved_text"] = visible_text(element)
        else:
            block["text"] = visible_text(element)
        blocks.append(block)
    side_content, warnings = [], set()
    warnings.update(block["structure_warning"] for block in blocks if "structure_warning" in block)
    tags = {W + tag: label for tag, label in [("drawing", "image_or_drawing"), ("pict", "image_or_shape"), ("txbxContent", "text_box"), ("ins", "tracked_changes"), ("del", "tracked_changes"), ("moveFrom", "tracked_changes"), ("moveTo", "tracked_changes"), ("fldChar", "field"), ("fldSimple", "field"), ("hyperlink", "hyperlink_not_followed"), ("sdt", "content_control"), ("object", "embedded_object"), ("altChunk", "alternate_content"), ("vanish", "hidden_text"), ("gridSpan", "merged_cells"), ("vMerge", "merged_cells")]}
    for name, element in parts.items():
        if not name.startswith("word/"):
            continue
        for node in element.iter():
            if node.tag in tags:
                warnings.add(tags[node.tag])
            if node.tag in (W + "customXml", W + "sym", W + "ptab") or "officeDocument/2006/math}" in node.tag:
                warnings.add("special_text_structure_requires_review")
            if "markup-compatibility/2006}" in node.tag:
                warnings.add("alternate_content_requires_review")
        if name != "word/document.xml" and any(label in name for label in ("header", "footer", "footnotes", "endnotes", "comments")):
            texts = [visible_text(p) for p in element.iter(W + "p")]
            if any(text.strip() for text in texts):
                side_content.append({"part": name, "paragraphs": texts})
                warnings.add("side_content_requires_review")
        if name.endswith(".rels"):
            if any(n.get("TargetMode") == "External" for n in element):
                warnings.add("external_relationship_not_followed")
    known = {"p", "tbl"}
    if any(block["type"] not in known for block in blocks):
        warnings.add("unrecognized_body_block")
    return {"kind": "source_inventory", "blocks": blocks, "side_content": side_content,
            "warnings": sorted(warnings), "requires_agent_review": True,
            "completeness": "text_inventory_only_not_visual_or_semantic_verification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        write_json_new(args.output, read_source(args.input))
    except (ContractError, OSError, ValueError) as exc:
        parser.exit(2, f"Cannot read source: {exc}\n")
    print("Text inventory written; Agent must review every block and warning.")


if __name__ == "__main__":
    main()
