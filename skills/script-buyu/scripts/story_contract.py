"""Validate authored story data. No authoring, model calls or production stages."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContractError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def read_json(path):
    def pairs(items):
        data = {}
        for key, value in items:
            require(key not in data, f"duplicate JSON key: {key}")
            data[key] = value
        return data
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=pairs)


def write_json_new(path, data):
    raw = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    write_bytes_new(path, raw.encode("utf-8"))


def _write_stream(stream, payload):
    stream.write(payload)
    stream.flush()
    os.fsync(stream.fileno())


def write_bytes_new(path, payload):
    """Publish a complete file without overwrite; fail on unsupported filesystems."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(str(target))
    temporary = target.with_name("." + target.name + "." + uuid.uuid4().hex + ".tmp")
    created = False
    try:
        with temporary.open("xb") as stream:
            created = True
            _write_stream(stream, payload)
        # Same-directory hard link is atomic and refuses any existing destination.
        # No copy fallback: unsupported filesystems must fail before publication.
        os.link(temporary, target)
    finally:
        if created:
            temporary.unlink(missing_ok=True)


def digest(data):
    def canonical(value):
        if isinstance(value, dict):
            return {key: canonical(item) for key, item in value.items()}
        if isinstance(value, list):
            return [canonical(item) for item in value]
        return int(value) if isinstance(value, float) and value.is_integer() else value
    raw = json.dumps(canonical(data), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def schema_check(value, schema, at="$"):
    """Restricted validator: fail on unimplemented keywords, not a general engine."""
    allowed = {"$schema", "title", "description", "type", "const", "enum", "properties", "required", "additionalProperties", "items", "minItems", "minLength", "pattern", "minimum", "exclusiveMinimum"}
    require(not set(schema).difference(allowed), "unsupported schema keywords")
    if "const" in schema:
        require(type(value) is type(schema["const"]) and value == schema["const"], f"{at}: wrong constant")
    if "enum" in schema:
        require(any(type(value) is type(option) and value == option for option in schema["enum"]), f"{at}: invalid option")
    types = {"object": lambda x: isinstance(x, dict), "array": lambda x: isinstance(x, list), "string": lambda x: isinstance(x, str), "integer": lambda x: type(x) is int, "number": lambda x: type(x) in (int, float) and math.isfinite(x), "null": lambda x: x is None}
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        require(all(name in types for name in names), "unsupported schema type")
        require(any(types[name](value) for name in names), f"{at}: expected {names}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        require(set(schema.get("required", [])) <= set(value), f"{at}: missing required fields")
        if schema.get("additionalProperties") is False:
            require(set(value) <= set(props), f"{at}: unsupported fields {set(value) - set(props)}")
        for key, child in props.items():
            if key in value:
                schema_check(value[key], child, at + "." + key)
    elif isinstance(value, list):
        require(len(value) >= schema.get("minItems", 0), f"{at}: empty collection")
        for index, child in enumerate(value):
            if "items" in schema:
                schema_check(child, schema["items"], f"{at}[{index}]")
    elif isinstance(value, str):
        require(len(value.strip()) >= schema.get("minLength", 0), f"{at}: empty text")
        require("\r" not in value, f"{at}: normalize CRLF or CR line endings to LF before validation")
        if "pattern" in schema:
            require(re.fullmatch(schema["pattern"], value) is not None, f"{at}: invalid identifier")
        require(not any(ord(char) < 32 and char not in "\t\n\r" for char in value), f"{at}: invalid control character")
    if type(value) in (int, float):
        require(math.isfinite(value), f"{at}: non-finite number")
        require(value >= schema.get("minimum", -math.inf), f"{at}: below minimum")
        require(value > schema.get("exclusiveMinimum", -math.inf), f"{at}: must be positive")


def unique(items, key, label):
    result = {}
    for item in items:
        require(item[key] not in result, f"duplicate {label}: {item[key]}")
        result[item[key]] = item
    return result


def validate_story(story):
    schema_check(story, read_json(ROOT / "schemas" / "screenplay.schema.json"))
    characters = unique(story["characters"], "character_id", "character")
    names = [item["name"] for item in characters.values()]
    require(len(set(names)) == len(names), "duplicate display names")
    require(all(name == name.strip() and "：" not in name and "\n" not in name and "\r" not in name for name in names), "ambiguous speaker name")
    episodes = unique(story["episodes"], "episode_id", "episode")
    unique(story["scenes"], "scene_id", "scene")
    require(len(episodes) == story["project"]["episode_count"], "episode count mismatch")
    require(abs(sum(ep["target_duration_seconds"] for ep in episodes.values()) - story["project"]["target_duration_seconds"]) < .001, "duration budget mismatch")
    order = {key: index for index, key in enumerate(episodes)}
    scene_order, beats = [], set()
    for scene in story["scenes"]:
        require(scene["episode_id"] in episodes, "unknown episode")
        scene_order.append(order[scene["episode_id"]])
        for beat in scene["beats"]:
            require(beat["beat_id"] not in beats, "duplicate beat")
            beats.add(beat["beat_id"])
            if beat["kind"] == "dialogue":
                require(beat["speaker_id"] in characters, "unknown speaker")
            else:
                require(beat["speaker_id"] is None, "action has a speaker")
            # Detect unfilled fields, not ordinary dialogue containing these words.
            require(not re.fullmatch(r"\s*(?:TODO|TBD|PLACEHOLDER|待填写|待补充|同上|\{\{.*\}\})\s*", beat["text"], re.I), "unfilled story beat")
    require(scene_order == sorted(scene_order), "scene order crosses episode order")
    require(set(scene["episode_id"] for scene in story["scenes"]) == set(episodes), "episode has no scenes")
    return story
