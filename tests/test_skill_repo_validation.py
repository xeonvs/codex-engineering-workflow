from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from test_support import load_script_module


validate_skill_repo = load_script_module("validate_skill_repo")
REPO_ROOT = Path(__file__).resolve().parents[1]
CURRENT_VERSION = "0.5.0"


class SkillRepoValidationTests(unittest.TestCase):
    def _copy_repo_subset(self, target: Path) -> None:
        shutil.copy2(REPO_ROOT / "README.md", target / "README.md")
        shutil.copy2(REPO_ROOT / "LICENSE", target / "LICENSE")
        shutil.copytree(REPO_ROOT / ".github", target / ".github")
        shutil.copytree(REPO_ROOT / "skill", target / "skill")

    def test_current_repo_layout_passes(self):
        result = validate_skill_repo.validate_skill_repo(REPO_ROOT)
        self.assertTrue(result["success"], result)
        self.assertEqual(result["skill_version"], CURRENT_VERSION)

    def test_forbidden_cache_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            cache = root / "skill" / "engineering-workflow" / "scripts" / "__pycache__"
            cache.mkdir(parents=True, exist_ok=True)
            (cache / "temp.pyc").write_bytes(b"compiled")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Forbidden cache path" in item for item in result["errors"]))

    def test_root_plans_workstation_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            private_path = "/" + "Users" + "/sample/private/project"
            (root / "PLANS.md").write_text("# Plans\n\n" + private_path, encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("macos_user_path" in item and "PLANS.md" in item for item in result["errors"]))

    def test_public_scan_does_not_follow_nonrequired_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            outside = root.parent / (root.name + "-outside.txt")
            key_name = "pass" + "word"
            outside.write_text(key_name + "=" + "not-for-publication", encoding="utf-8")
            try:
                (root / "linked.txt").symlink_to(outside)
                result = validate_skill_repo.validate_skill_repo(root)
                self.assertTrue(result["success"], result)
            finally:
                outside.unlink(missing_ok=True)

    def test_missing_skill_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "skill" / "engineering-workflow" / "SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(f"metadata:\n  version: {CURRENT_VERSION}\n", ""),
                encoding="utf-8",
            )
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("metadata.version" in item for item in result["errors"]))

    def test_readme_version_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "README.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    f"Current skill version: `{CURRENT_VERSION}`.",
                    "Current skill version: `0.4.1`.",
                ),
                encoding="utf-8",
            )
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("current skill version" in item for item in result["errors"]))

    def test_legitimate_historical_version_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "README.md"
            path.write_text(path.read_text(encoding="utf-8") + "\nHistorical release: 0.4.1.\n", encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertTrue(result["success"], result)

    def test_active_manifest_version_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            manifest = root / "docs" / "codex" / "ENGINEERING_WORKFLOW_STATE.yaml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("schema_version: 1\nskill_version: \"0.4.1\"\n", encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("manifest version" in item for item in result["errors"]))

    def test_missing_plan_section_is_rejected_structurally(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "skill" / "engineering-workflow" / "assets" / "templates" / "PLANS.md.tmpl"
            path.write_text(path.read_text(encoding="utf-8").replace("### Resume Point", "### Continuation Notes"), encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("missing plan section: Resume Point" in item for item in result["errors"]))

    def test_missing_reconciliation_marker_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "skill" / "engineering-workflow" / "references" / "planning_and_backlog.md"
            path.write_text(path.read_text(encoding="utf-8").replace("## Resume And Milestone Reconciliation", "## State Review"), encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("reconciliation" in item.lower() for item in result["errors"]))

    def test_duplicate_canonical_owner_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "skill" / "engineering-workflow" / "references" / "merge_policy.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n## Full Active Plan Schema\n", encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Canonical owner mismatch" in item for item in result["errors"]))

    def test_model_slug_outside_owner_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "skill" / "engineering-workflow" / "references" / "merge_policy.md"
            model = "gpt-" + "5.6-" + "terra"
            path.write_text(path.read_text(encoding="utf-8") + f"\nModel: `{model}`.\n", encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Concrete model mapping" in item for item in result["errors"]))

    def test_invented_pro_slug_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "README.md"
            invented = "gpt-" + "5.6-" + "pro"
            path.write_text(path.read_text(encoding="utf-8") + f"\n{invented}\n", encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("invented pro model slug" in item for item in result["errors"]))

    def test_missing_refresh_section_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "README.md"
            path.write_text(path.read_text(encoding="utf-8").replace("## Refresh Loaded Skill", "## Reload Notes"), encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Refresh Loaded Skill" in item for item in result["errors"]))

    def test_invalid_optional_agent_toml_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "skill" / "engineering-workflow" / "assets" / "agents" / "utility.toml.tmpl"
            path.write_text('name = "unterminated\n', encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Parse failure" in item for item in result["errors"]))

    def test_validator_does_not_pin_long_contract_prose(self):
        source = (REPO_ROOT / "skill" / "engineering-workflow" / "scripts" / "validate_skill_repo.py").read_text(encoding="utf-8")
        legacy_name = "REQUIRED_" + "CONTRACT_SNIPPETS"
        self.assertNotIn(legacy_name, source)


if __name__ == "__main__":
    unittest.main()
