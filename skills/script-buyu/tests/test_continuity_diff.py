"""Behavioral invariants of the diff helper, not literary quality tests."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_story_versions import compare_stories
from story_contract import ContractError
from fixtures import story


class ContinuityDiffTests(unittest.TestCase):
    def test_unchanged_is_not_semantic_or_approval_pass(self):
        result = compare_stories(story(), story())
        self.assertEqual(result["changes"], [])
        self.assertFalse(result["content_changed"])
        self.assertEqual(result["status"], "comparison_only")
        self.assertFalse(result["review_scope_hint"]["dependencies_complete"])

    def test_same_revision_changed_ending_detected(self):
        old, new = story(), story()
        new["scenes"][-1]["beats"][-1]["text"] = "渡船继续驶向远方。"
        result = compare_stories(old, new)
        self.assertTrue(result["same_revision_content_changed"])
        self.assertEqual(result["review_scope_hint"]["direct_scene_ids"], [new["scenes"][-1]["scene_id"]])

    def test_revision_only_changes_identity_not_content(self):
        new = story()
        new["revision"] += 1
        result = compare_stories(story(), new)
        self.assertFalse(result["content_changed"])
        self.assertNotEqual(result["before_digest"], result["after_digest"])
        self.assertEqual(result["changes"][0]["path"], "/revision")

    def test_same_words_different_speaker_is_a_change(self):
        new = story()
        new["scenes"][0]["beats"][1]["speaker_id"] = "C2"
        result = compare_stories(story(), new)
        self.assertTrue(any(c["path"].endswith("/speaker_id") for c in result["changes"]))

    def test_repeated_dialogue_is_not_deduplicated(self):
        old = story()
        duplicate = copy.deepcopy(old["scenes"][0]["beats"][1])
        duplicate["beat_id"] = "B99"
        old["scenes"][0]["beats"].append(duplicate)
        result = compare_stories(old, story())
        self.assertTrue(any(c["kind"] == "removed" and c["path"].endswith("/B99") for c in result["changes"]))

    def test_reorder_preserving_all_words_is_detected(self):
        new = story()
        new["scenes"][0]["beats"].reverse()
        result = compare_stories(story(), new)
        self.assertTrue(any(c["kind"] == "sequence_changed" for c in result["changes"]))
        self.assertTrue(result["content_changed"])

    def test_world_change_requires_shared_review(self):
        new = story()
        new["world_rules"][0] = "备用电池可以持续同时供电。"
        result = compare_stories(story(), new)
        self.assertTrue(result["review_scope_hint"]["shared_fields_changed"])
        self.assertFalse(result["review_scope_hint"]["dependencies_complete"])

    def test_visual_prompt_added_is_not_ignored(self):
        new = story()
        for c in new["characters"]:
            c["visual_prompt"] = "本剧人物，清晰参考画像。"
        result = compare_stories(story(), new)
        self.assertTrue(result["content_changed"])
        self.assertEqual(sum(c["path"].endswith("/visual_prompt") for c in result["changes"]), 2)

    def test_punctuation_is_not_silently_normalized(self):
        new = story()
        new["scenes"][0]["beats"][1]["text"] += "！"
        self.assertTrue(compare_stories(story(), new)["content_changed"])

    def test_invalid_unknown_speaker_rejected(self):
        new = story()
        new["scenes"][0]["beats"][1]["speaker_id"] = "UNKNOWN"
        with self.assertRaises(ContractError):
            compare_stories(story(), new)

    def test_inputs_unchanged_and_result_detached(self):
        old, new = story(), story()
        new["world_rules"] = ["新的供电规则。"]
        saved = copy.deepcopy((old, new))
        result = compare_stories(old, new)
        result["changes"][0]["after"].append("不能改到原稿")
        self.assertEqual((old, new), saved)


if __name__ == "__main__":
    unittest.main()
