from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from test_support import load_script_module


validate_skill_repo = load_script_module("validate_skill_repo")
REPO_ROOT = Path(__file__).resolve().parents[1]
CURRENT_VERSION = "0.3.1"
STALE_VERSION = ".".join(["0", "3", "0"])
LEGACY_COMPACT_QUEUE = "compact checked " + "queue item"


class SkillRepoValidationTests(unittest.TestCase):
    def _copy_repo_subset(self, target: Path) -> None:
        shutil.copy2(REPO_ROOT / "README.md", target / "README.md")
        shutil.copy2(REPO_ROOT / "LICENSE", target / "LICENSE")
        shutil.copytree(REPO_ROOT / ".github", target / ".github")
        shutil.copytree(REPO_ROOT / "skill", target / "skill")

    def test_current_repo_layout_passes(self):
        result = validate_skill_repo.validate_skill_repo(REPO_ROOT)
        self.assertTrue(result["success"], result)

    def test_forbidden_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._copy_repo_subset(repo_root)
            cache_dir = repo_root / "skill" / "engineering-workflow" / "scripts" / "__pycache__"
            cache_dir.mkdir(parents=True, exist_ok=True)
            (cache_dir / "temp.pyc").write_bytes(b"compiled")

            result = validate_skill_repo.validate_skill_repo(repo_root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Forbidden cache path" in item for item in result["errors"]))

    def test_absolute_home_path_in_readme_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._copy_repo_subset(repo_root)
            readme = repo_root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + ('\n/h' 'ome/example/private/skill\n'),
                encoding="utf-8",
            )

            result = validate_skill_repo.validate_skill_repo(repo_root)
            self.assertFalse(result["success"])
            self.assertTrue(any("absolute_home_path" in item for item in result["errors"]))

    def test_missing_skill_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._copy_repo_subset(repo_root)
            skill_md = repo_root / "skill" / "engineering-workflow" / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    f"metadata:\n  version: {CURRENT_VERSION}\n",
                    "",
                ),
                encoding="utf-8",
            )

            result = validate_skill_repo.validate_skill_repo(repo_root)
            self.assertFalse(result["success"])
            self.assertTrue(any("metadata.version" in item for item in result["errors"]))

    def test_readme_version_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._copy_repo_subset(repo_root)
            readme = repo_root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(f"Current skill version: `{CURRENT_VERSION}`.", "Current skill version: `0.2.0`."),
                encoding="utf-8",
            )

            result = validate_skill_repo.validate_skill_repo(repo_root)
            self.assertFalse(result["success"])
            self.assertTrue(any("current skill version" in item for item in result["errors"]))

    def test_stale_skill_version_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._copy_repo_subset(repo_root)
            readme = repo_root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + f"\nPrior version: {STALE_VERSION}\n",
                encoding="utf-8",
            )

            result = validate_skill_repo.validate_skill_repo(repo_root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Stale skill version" in item for item in result["errors"]))

    def test_legacy_compact_planning_language_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._copy_repo_subset(repo_root)
            template = repo_root / "skill" / "engineering-workflow" / "assets" / "templates" / "PLANS.md.tmpl"
            template.write_text(
                template.read_text(encoding="utf-8") + f"\nUse a {LEGACY_COMPACT_QUEUE}.\n",
                encoding="utf-8",
            )

            result = validate_skill_repo.validate_skill_repo(repo_root)
            self.assertFalse(result["success"])
            self.assertTrue(any("legacy_compact_queue_contract" in item for item in result["errors"]))

    def test_missing_resume_point_contract_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._copy_repo_subset(repo_root)
            template = repo_root / "skill" / "engineering-workflow" / "assets" / "templates" / "PLANS.md.tmpl"
            template.write_text(
                template.read_text(encoding="utf-8").replace("\n### Resume Point\n", "\n### Continuation Notes\n"),
                encoding="utf-8",
            )

            result = validate_skill_repo.validate_skill_repo(repo_root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Required planning contract text" in item for item in result["errors"]))

    def test_missing_planning_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._copy_repo_subset(repo_root)
            (repo_root / "skill" / "engineering-workflow" / "references" / "planning_and_backlog.md").unlink()

            result = validate_skill_repo.validate_skill_repo(repo_root)
            self.assertFalse(result["success"])
            self.assertTrue(any("planning_and_backlog.md" in item for item in result["errors"]))

    def test_missing_forced_refresh_prompt_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self._copy_repo_subset(repo_root)
            readme = repo_root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace("## Forced Skill Refresh Prompt", "## Removed Refresh Prompt"),
                encoding="utf-8",
            )

            result = validate_skill_repo.validate_skill_repo(repo_root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Forced Skill Refresh Prompt" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
