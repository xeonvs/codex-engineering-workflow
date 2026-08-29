import importlib.util
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "dev_check.py"
SPEC = importlib.util.spec_from_file_location("dev_check", MODULE_PATH)
dev_check = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(dev_check)


class DevCheckTests(unittest.TestCase):
    def test_release_is_full_plus_pre_push_security(self):
        with tempfile.TemporaryDirectory() as temporary:
            log_dir = Path(temporary)
            full = dev_check.select_checks("full", log_dir=log_dir, test_pattern=None, fix=False)
            security = dev_check.select_checks("security", log_dir=log_dir, test_pattern=None, fix=False)
            release = dev_check.select_checks("release", log_dir=log_dir, test_pattern=None, fix=False)

        self.assertEqual(release, full + security)
        self.assertEqual(
            [check.name for check in security], ["public-tree-privacy", "gitleaks-tree", "gitleaks-history"]
        )
        history = security[-1].command
        self.assertIn("--redact=100", history)
        self.assertIn("--log-opts=--all", history)

    def test_focused_pattern_is_one_safe_test_basename(self):
        with tempfile.TemporaryDirectory() as temporary:
            log_dir = Path(temporary)
            checks = dev_check.select_checks(
                "focused",
                log_dir=log_dir,
                test_pattern="test_plan_lifecycle.py",
                fix=False,
            )
            self.assertEqual(len(checks), 1)
            self.assertIn("test_plan_lifecycle.py", checks[0].command)
            for unsafe in (None, "plan_lifecycle.py", "../test_escape.py", "test_*.py"):
                with self.assertRaises(ValueError):
                    dev_check.select_checks("focused", log_dir=log_dir, test_pattern=unsafe, fix=False)

    def test_fix_is_restricted_to_explicit_format_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            log_dir = Path(temporary)
            checks = dev_check.select_checks("format", log_dir=log_dir, test_pattern=None, fix=True)
            self.assertEqual([check.name for check in checks], ["ruff-version", "ruff-lint-fix", "ruff-format-fix"])
            with self.assertRaises(ValueError):
                dev_check.select_checks("full", log_dir=log_dir, test_pattern=None, fix=True)

    def test_child_environment_always_disables_bytecode(self):
        environment = dev_check.child_environment()
        self.assertEqual(environment["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(environment["PYTHONUNBUFFERED"], "1")

    def test_ruff_version_gate_requires_an_exact_version(self):
        check = dev_check._quality_checks()[0]
        self.assertEqual(check.expected_text, "ruff 0.16.4")
        self.assertEqual(check.command[-1], "--version")
        with tempfile.TemporaryDirectory() as temporary:
            log_dir = Path(temporary)
            near_match = dev_check.Check(
                "near-match",
                (dev_check.sys.executable, "-c", "print('ruff 0.16.40')"),
                "ruff 0.16.4",
            )
            self.assertNotEqual(dev_check._run_check(near_match, log_dir=log_dir).returncode, 0)

    def test_failure_output_stays_in_private_log(self):
        with tempfile.TemporaryDirectory() as temporary:
            log_dir = Path(temporary)
            log_dir.chmod(0o700)
            marker = "sensitive-child-output"
            check = dev_check.Check(
                "synthetic-failure", (dev_check.sys.executable, "-c", f"print('{marker}'); raise SystemExit(3)")
            )
            result = dev_check._run_check(check, log_dir=log_dir)

            self.assertEqual(result.returncode, 3)
            self.assertIn(marker, result.log_path.read_text(encoding="utf-8"))
            self.assertEqual(stat.S_IMODE(log_dir.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(result.log_path.stat().st_mode), 0o600)

    def test_default_summary_does_not_read_or_print_failure_log(self):
        result = dev_check.CheckResult("failed", "FAIL", 1, 0.01, Path("not-read-by-default"))
        with mock.patch.object(Path, "read_text", side_effect=AssertionError("log read")):
            dev_check._print_failure_tail(result, 0)

    def test_harness_is_not_distributed_with_the_skill(self):
        self.assertFalse((REPO_ROOT / "skill" / "engineering-workflow" / "scripts" / "dev_check.py").exists())
        self.assertFalse(
            (
                REPO_ROOT
                / "plugins"
                / "engineering-workflow"
                / "skills"
                / "engineering-workflow"
                / "scripts"
                / "dev_check.py"
            ).exists()
        )

    def test_target_agents_receive_the_pre_push_secret_gate_without_the_harness(self):
        privacy_contract = (
            REPO_ROOT / "skill" / "engineering-workflow" / "references" / "privacy_and_sanitization.md"
        ).read_text(encoding="utf-8")
        principles = (
            REPO_ROOT / "skill" / "engineering-workflow" / "assets" / "templates" / "project_principles.md.tmpl"
        ).read_text(encoding="utf-8")

        self.assertIn("## Pre-Push Secret Gate", privacy_contract)
        self.assertIn("Before every authorized push", principles)
        self.assertNotIn("scripts/dev_check.py", principles)


if __name__ == "__main__":
    unittest.main()
