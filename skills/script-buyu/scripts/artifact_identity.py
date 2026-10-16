"""Artifact purpose and bound lineage; never certifies creative quality or timing."""
from pathlib import Path
import hashlib
import json
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from story_contract import ContractError, digest, require, read_json, write_json_new

PREFIX = "script-buyu/artifact-purpose/1:"
PURPOSES = {"engineering", "work_draft", "unknown"}
FIXTURE_CORE_DIGEST = "bd30259a0418e224e827b8483ec0e734946905ec0f7a8eda3f8621a54810cda7"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def receipt_path(path):
    return Path(str(path) + ".identity.json")


def story_purpose(story, inherited="unknown", declared="auto"):
    require(inherited in PURPOSES and declared in PURPOSES | {"auto"}, "invalid artifact purpose")
    try:
        core = {k: story[k] for k in ("logline", "synopsis", "world_rules", "scenes")}
        core["characters"] = [{k:r[k] for k in ("character_id", "name", "description", "arc")} for r in story["characters"]]
        copied_core = digest(core) == FIXTURE_CORE_DIGEST
        registered_shape = (story["project"]["project_id"] == "TEST-LIGHT"
            and [(r["character_id"], r["name"]) for r in story["characters"]] == [("C1", "阿砚"), ("C2", "陆禾")]
            and [r["scene_id"] for r in story["scenes"]] == ["S1", "S2"]
            and [b["beat_id"] for r in story["scenes"] for b in r["beats"]] == ["B"+str(i) for i in range(1,10)]
            and story["world_rules"] == ["备用电池只能承担一种持续负载，间歇发光可以降低耗电。"])
    except (KeyError, TypeError):
        return "engineering" if inherited == "engineering" else "unknown"
    purpose = "engineering" if copied_core or registered_shape or inherited == "engineering" or declared == "engineering" else "work_draft"
    require(not (purpose == "engineering" and declared == "work_draft"), "engineering fixture lineage cannot be relabeled as a work draft")
    return purpose


def artifact_purpose(path, story=None, declared="auto"):
    """Use content identity, package marker or bound source record; not filenames/titles."""
    path = Path(path)
    inherited = "unknown"
    sidecar = receipt_path(path)
    if sidecar.exists():
        data = read_json(sidecar)
        require(data.get("purpose") in PURPOSES, "invalid identity sidecar")
        # Engineering origin survives an edit; stale positive records grant no result.
        if data["purpose"] == "engineering":
            inherited = "engineering"
        elif data.get("artifact_sha256") == sha(path):
            inherited = data["purpose"]
    if path.suffix.casefold() in {".docx", ".xlsx"}:
        with ZipFile(path) as package:
            if "docProps/core.xml" in package.namelist():
                root = ET.fromstring(package.read("docProps/core.xml"))
                category = root.find("{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}category")
                if category is not None and (category.text or "").startswith(PREFIX):
                    value = category.text[len(PREFIX):]
                    require(value in PURPOSES, "invalid embedded purpose marker")
                    inherited = "engineering" if value == "engineering" or inherited == "engineering" else value
    if story is None and path.suffix.casefold() == ".json":
        data = read_json(path)
        story = data if isinstance(data,dict) and "project" in data else None
    if story is None and path.suffix.casefold() == ".docx":
        from screenplay_docx import extract_docx
        try:
            story = extract_docx(path)
        except ContractError:
            # External documents stay unknown until a concrete source is declared.
            pass
    if story is not None:
        return story_purpose(story,inherited,declared)
    require(declared in PURPOSES | {"auto"}, "invalid artifact purpose")
    require(not (inherited == "engineering" and declared == "work_draft"), "engineering source cannot be relabeled")
    return inherited if inherited != "unknown" else (declared if declared != "auto" else "unknown")


def write_receipt(output, purpose, source=None, story=None, source_purpose=None):
    require(purpose in PURPOSES, "invalid artifact purpose")
    observed = artifact_purpose(source) if source is not None else "unknown"
    require(not (observed == "engineering" and purpose != "engineering"), "engineering source must retain engineering purpose")
    if source_purpose is not None:
        require(source_purpose in PURPOSES, "invalid source purpose")
    data = {"identity_version":1,"purpose":purpose,"artifact_sha256":sha(output),
            "content_quality":"not_certified","visual_quality":"not_certified",
            "duration_assertion":"budget_metadata_only_not_elapsed_time"}
    if source is not None:
        data["source"] = {"path":str(Path(source).resolve()),"sha256":sha(source),"purpose":source_purpose or observed,"purpose_basis":"explicit_source_declaration" if source_purpose is not None and observed == "unknown" else "observed_source_identity"}
    if story is not None:
        data["visible_story_digest"] = digest(story)
    write_json_new(receipt_path(output),data)
    return data
