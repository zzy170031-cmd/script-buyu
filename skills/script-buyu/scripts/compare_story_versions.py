"""Read-only exact story-data diff. Never infers semantics, approval or dependencies."""
from __future__ import annotations

import argparse
import copy
import json

from story_contract import ContractError, digest, read_json, validate_story


COLLECTION_IDS = {
    "characters": "character_id", "episodes": "episode_id",
    "scenes": "scene_id", "beats": "beat_id",
}


def content_digest(story):
    # A content identity is not an approval and does not ignore punctuation.
    return digest({k: v for k, v in story.items() if k not in {"revision", "status"}})


def compare_stories(before, after):
    validate_story(before)
    validate_story(after)
    changes, direct_scenes = [], set()

    def emit(path, kind, old, new, scene_id=None):
        changes.append({"path": path, "kind": kind,
                        "before": copy.deepcopy(old), "after": copy.deepcopy(new)})
        if scene_id is not None:
            direct_scenes.add(scene_id)

    def walk(old, new, path="", collection=None, scene_id=None):
        if old == new:
            return
        if isinstance(old, dict) and isinstance(new, dict):
            for key in sorted(set(old) | set(new)):
                child = path + "/" + key.replace("~", "~0").replace("/", "~1")
                if key not in old:
                    emit(child, "added", None, new[key], scene_id)
                elif key not in new:
                    emit(child, "removed", old[key], None, scene_id)
                else:
                    walk(old[key], new[key], child, key, scene_id)
        elif isinstance(old, list) and isinstance(new, list) and collection in COLLECTION_IDS:
            key = COLLECTION_IDS[collection]
            old_ids, new_ids = [v[key] for v in old], [v[key] for v in new]
            if old_ids != new_ids:
                emit(path + "/@order", "sequence_changed", old_ids, new_ids, scene_id)
                if collection == "scenes":
                    direct_scenes.update(old_ids + new_ids)
            left, right = {v[key]: v for v in old}, {v[key]: v for v in new}
            for identity in dict.fromkeys(old_ids + new_ids):
                scope = identity if collection == "scenes" else scene_id
                child = path + "/" + identity
                if identity not in left:
                    emit(child, "added", None, right[identity], scope)
                elif identity not in right:
                    emit(child, "removed", left[identity], None, scope)
                else:
                    walk(left[identity], right[identity], child, scene_id=scope)
        else:
            emit(path, "changed", old, new, scene_id)

    walk(before, after)
    content_changed = content_digest(before) != content_digest(after)
    global_roots = {"characters", "episodes", "world_rules", "project", "logline", "synopsis"}
    return {
        "status": "comparison_only",
        "before_digest": digest(before), "after_digest": digest(after),
        "before_content_digest": content_digest(before),
        "after_content_digest": content_digest(after),
        "content_changed": content_changed,
        "same_revision_content_changed": before["revision"] == after["revision"] and content_changed,
        "changes": changes,
        "review_scope_hint": {
            "direct_scene_ids": sorted(direct_scenes),
            "shared_fields_changed": any(c["path"].split("/")[1] in global_roots for c in changes),
            "dependencies_complete": False,
        },
        "limitations": "Exact data comparison only. No semantic, authorization, approval, "
                       "DOCX/XLSX fidelity or complete dependency validation. Read actual source and affected text.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    args = parser.parse_args()
    try:
        result = compare_stories(read_json(args.before), read_json(args.after))
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit("Story comparison failed: " + str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
