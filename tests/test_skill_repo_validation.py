from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from test_support import load_script_module


validate_skill_repo = load_script_module("validate_skill_repo")
REPO_ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
