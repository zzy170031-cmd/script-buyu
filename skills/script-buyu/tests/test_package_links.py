import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_skill import ContractError, validate_package_links


class InstalledPackageTests(unittest.TestCase):
    def test_reference_must_travel_with_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skill"
            notes = root / "references" / "study-notes"
            notes.mkdir(parents=True)
            (root / "SKILL.md").write_text("[notes](references/study-notes/)", encoding="utf-8")
            page = notes / "notes.md"
            page.write_text("[more](#details)", encoding="utf-8")
            validate_package_links(root)
            sibling = Path(temp) / "report.md"
            sibling.touch()
            for link in ("../../../report.md", "missing.md"):
                with self.subTest(link=link):
                    page.write_text(f"[more]({link})", encoding="utf-8")
                    with self.assertRaises(ContractError):
                        validate_package_links(root)

    def test_marker_matches_actual_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            refs = root / "references"
            refs.mkdir()
            (root / "SKILL.md").touch()
            prompt = refs / "storyboard-prompt-current.txt"
            prompt.write_bytes(b"original\n")
            marker = {"prompt_sha256": hashlib.sha256(prompt.read_bytes()).hexdigest()}
            (root / "WORKBUDDY_PACKAGE_VERSION.json").write_text(json.dumps(marker), encoding="utf-8")
            validate_package_links(root)
            prompt.write_bytes(b"changed\n")
            with self.assertRaisesRegex(ContractError, "WorkBuddy"):
                validate_package_links(root)
