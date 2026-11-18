"""Offline structural check; not a substitute for Agent or literary evaluation."""
import ast
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from story_contract import ROOT, ContractError, read_json, require, unique


def validate_package_links(root):
    root = root.resolve()
    references = root / "references"
    pages = [root / "SKILL.md", *references.glob("*.md"), *(references / "study-notes").glob("*.md")]
    for page in pages:
        for link in re.findall(r"\]\(([^)]+)\)", page.read_text(encoding="utf-8")):
            url = urlparse(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (page.parent / unquote(url.path)).resolve()
            exists = target.is_dir() if url.path.endswith("/") else target.is_file()
            require(target.is_relative_to(root) and exists,
                    f"missing or nonportable link in {page.relative_to(root)}: {link}")

    marker = root / "WORKBUDDY_PACKAGE_VERSION.json"
    if marker.exists():
        declared = read_json(marker)
        prompt = references / "storyboard-prompt-current.txt"
        actual = hashlib.sha256(prompt.read_bytes()).hexdigest()
        require(isinstance(declared, dict) and declared.get("prompt_sha256") == actual,
                "WorkBuddy marker does not match the installed storyboard prompt")


def validate_skill(root=ROOT):
    entry = (root / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", entry, re.S)
    require(match is not None, "missing YAML frontmatter")
    # This package deliberately uses the supported scalar-only YAML subset.
    fields = dict(line.split(": ", 1) for line in match[1].splitlines())
    require(set(fields) == {"name", "description"}, "unexpected frontmatter fields")
    require(fields["name"] == "script-buyu" and len(fields["description"]) > 20, "invalid Skill routing metadata")
    require(len(entry.splitlines()) < 250, "entrypoint too long")
    for relative in re.findall(r"`((?:references|data|schemas|scripts)/[^`\s]+)`", entry):
        require((root / relative).is_file(), "missing resource: " + relative)
    validate_package_links(root)
    require("--docx " not in entry and "--out " not in entry, "stale CLI examples")
    yaml = (root / "agents/openai.yaml").read_text(encoding="utf-8")
    for key in ("display_name", "short_description", "default_prompt"):
        require(re.search(r'^  ' + key + r': ".+"$', yaml, re.M), "invalid UI metadata: " + key)
    short = re.search(r'  short_description: "(.+)"', yaml)[1]
    require(25 <= len(short) <= 64, "short_description length")
    require("$script-buyu" in yaml, "default prompt does not name this Skill")
    library = read_json(root / "data/story-methods.json")
    sources = unique(library["sources"], "source_id", "method source")
    methods = unique(library["methods"], "method_id", "method")
    for source in sources.values():
        for key in ("name", "professional_role", "project_evidence", "source_type", "evidence_summary", "accessed_at", "limitations", "read_status"):
            require(bool(source.get(key)), "incomplete source: " + key)
        require(source["entity_type"] in ("person", "team"), "invalid entity type")
        require(urlparse(source["url"]).scheme == "https", "source must be an HTTPS URL")
    for method in methods.values():
        require(method["kind"] in ("public_method_adaptation", "editorial_heuristic"), "unknown method kind")
        require(set(method["source_ids"]) <= set(sources), "unknown method source")
        require(bool(method["source_ids"]) == (method["kind"] == "public_method_adaptation"), "method evidence label mismatch")
        require(len(method["steps"]) >= 2 and method["check"] and method["limits"], "method lacks operational content")
    candidates = read_json(root / "data/expert-candidates.json")
    require("unverified" in candidates["status"], "candidate qualification is overstated")
    unique(candidates["candidates"], "expert_id", "candidate")
    for path in (root / "scripts").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=path.name)
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        require(not any(name and name.split(".")[0] == "production_contract" for name in imports), "nonportable production dependency")
        literals = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
        require(not any(re.match(r"^[A-Za-z]:[\\/]", value) for value in literals), "absolute runtime path")
    read_json(root / "schemas/screenplay.schema.json")
    from query_methods import validate_index
    genre_coverage = validate_index(read_json(root / "data/genre-index.json"), library)
    return {"status": "structural_checks_passed", "sources": len(sources), "methods": len(methods),
            "candidate_entries": len(candidates["candidates"]),
            "genre_coverage": genre_coverage,
            "limitations": "Does not prove Agent routing, literary quality, source freshness or rendered layout."}


if __name__ == "__main__":
    try:
        print(json.dumps(validate_skill(), ensure_ascii=False))
    except (ContractError, OSError, ValueError, KeyError) as exc:
        raise SystemExit("Skill validation failed: " + str(exc))
