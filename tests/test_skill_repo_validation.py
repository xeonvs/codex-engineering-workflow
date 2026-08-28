from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_support import load_script_module


validate_skill_repo = load_script_module("validate_skill_repo")
REPO_ROOT = Path(__file__).resolve().parents[1]
CURRENT_VERSION = "0.8.2"


class SkillRepoValidationTests(unittest.TestCase):
    def _copy_repo_subset(self, target: Path) -> None:
        shutil.copy2(REPO_ROOT / "README.md", target / "README.md")
        shutil.copy2(REPO_ROOT / "AGENTS.md", target / "AGENTS.md")
        shutil.copy2(REPO_ROOT / "LICENSE", target / "LICENSE")
        if (REPO_ROOT / "PLANS.md").exists():
            shutil.copy2(REPO_ROOT / "PLANS.md", target / "PLANS.md")
        shutil.copytree(REPO_ROOT / ".github", target / ".github")
        shutil.copytree(REPO_ROOT / ".agents", target / ".agents")
        shutil.copytree(REPO_ROOT / ".claude-plugin", target / ".claude-plugin")
        shutil.copytree(REPO_ROOT / "docs", target / "docs")
        shutil.copytree(REPO_ROOT / "plugins", target / "plugins")
        shutil.copytree(
            REPO_ROOT / "scripts",
            target / "scripts",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        shutil.copytree(
            REPO_ROOT / "skill",
            target / "skill",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )

    def test_current_repo_layout_passes_in_clean_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertTrue(result["success"], result)
            self.assertEqual(result["skill_version"], CURRENT_VERSION)

    def test_root_agents_is_local_and_not_packaged_with_skill(self):
        text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("not part of the installed", text)
        self.assertFalse((REPO_ROOT / "skill/engineering-workflow/AGENTS.md").exists())

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

    def test_cli_does_not_create_cache_without_bytecode_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            script = root / "skill" / "engineering-workflow" / "scripts" / "validate_skill_repo.py"
            env = os.environ.copy()
            env.pop("PYTHONDONTWRITEBYTECODE", None)
            env.pop("PYTHONPYCACHEPREFIX", None)

            completed = subprocess.run(
                [sys.executable, str(script), "--repo-root", str(root)],
                cwd=root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 0, completed.stderr or payload)
            self.assertTrue(payload["success"], payload)
            self.assertEqual(list(root.rglob("__pycache__")), [])
            self.assertEqual(list(root.rglob("*.pyc")), [])

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
            path.write_text(path.read_text(encoding="utf-8").replace("## Refresh a loaded skill", "## Reload notes"), encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Refresh a loaded skill" in item for item in result["errors"]))

    def test_installation_for_both_agents_precedes_workflow_internals(self):
        text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        install = text.index("## Install with Codex or Claude Code")
        quick_start = text.index("## Quick start")
        internals = text.index("## Planning and backlog lifecycle")
        self.assertLess(install, quick_start)
        self.assertLess(quick_start, internals)
        self.assertIn("codex plugin add engineering-workflow@xeonvs-engineering", text)
        self.assertIn("claude plugin install engineering-workflow@xeonvs-engineering", text)
        self.assertIn("/engineering-workflow:engineering-workflow", text)

    def test_runtime_router_explains_privacy_approval_without_value_access(self):
        text = (REPO_ROOT / "skill/engineering-workflow/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("request_privacy_review_approval", text)
        self.assertIn("do not open the flagged lines", text)
        self.assertIn("Never approve on the user's behalf", text)

    def test_disabled_implicit_invocation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "skill" / "engineering-workflow" / "agents" / "openai.yaml"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "allow_implicit_invocation: true",
                    "allow_implicit_invocation: false",
                ),
                encoding="utf-8",
            )
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("implicit invocation" in item for item in result["errors"]))

    def test_missing_prompt_upgrade_backend_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "README.md"
            path.write_text(path.read_text(encoding="utf-8").replace("--prompt", "--plan", 1), encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("prompt-owned target-upgrade" in item for item in result["errors"]))

    def test_invalid_optional_agent_toml_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "skill" / "engineering-workflow" / "assets" / "agents" / "utility.toml.tmpl"
            path.write_text('name = "unterminated\n', encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Parse failure" in item for item in result["errors"]))

    def test_unterminated_yaml_scalar_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            path = root / "skill" / "engineering-workflow" / "agents" / "openai.yaml"
            path.write_text('interface:\n  display_name: "unterminated\n', encoding="utf-8")
            result = validate_skill_repo.validate_skill_repo(root)
            self.assertFalse(result["success"])
            self.assertTrue(any("Parse failure" in item and "openai.yaml" in item for item in result["errors"]))

    @unittest.skipUnless(os.name == "posix", "non-UTF-8 Git paths require POSIX byte paths")
    def test_non_utf8_tracked_path_does_not_crash_public_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_repo_subset(root)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            raw_root = os.fsencode(root)
            raw_name = b"non-utf8-\xff.txt"
            try:
                descriptor = os.open(raw_root + b"/" + raw_name, os.O_WRONLY | os.O_CREAT, 0o600)
            except OSError as exc:
                self.skipTest(f"filesystem rejects non-UTF-8 names: {exc.errno}")
            try:
                os.write(descriptor, b"plain text\n")
            finally:
                os.close(descriptor)
            subprocess.run([b"git", b"-C", raw_root, b"add", b"--", raw_name], check=True)

            result = validate_skill_repo.validate_skill_repo(root)

            self.assertTrue(result["success"], result)

    def test_ci_revalidates_after_tests_with_bytecode_disabled(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        command = "python skill/engineering-workflow/scripts/validate_skill_repo.py --repo-root ."
        first = workflow.find(command)
        tests = workflow.find("python -m unittest discover -s tests -v")
        second = workflow.find(command, first + 1)
        self.assertIn('PYTHONDONTWRITEBYTECODE: "1"', workflow)
        self.assertGreater(first, -1)
        self.assertGreater(tests, first)
        self.assertGreater(second, tests)

    def test_ci_actions_use_node24_majors(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("actions/checkout@v6", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertNotIn("actions/checkout@v4", workflow)
        self.assertNotIn("actions/setup-python@v5", workflow)

    def test_validator_does_not_pin_long_contract_prose(self):
        source = (REPO_ROOT / "skill" / "engineering-workflow" / "scripts" / "validate_skill_repo.py").read_text(encoding="utf-8")
        legacy_name = "REQUIRED_" + "CONTRACT_SNIPPETS"
        self.assertNotIn(legacy_name, source)


if __name__ == "__main__":
    unittest.main()
