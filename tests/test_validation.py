from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module

FIXTURES = Path(__file__).resolve().parent / "fixtures"
common = load_script_module("common")
validate_target_repo = load_script_module("validate_target_repo")


class ValidationTests(unittest.TestCase):
    def test_execution_reference_preserves_correctness_and_evidence_boundaries(self):
        reference = (
            Path(__file__).resolve().parents[1] / "skill/engineering-workflow/references/validation_safety.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Optimize inspection and execution only after correctness", reference)
        self.assertIn("one bounded reconnaissance pass", reference)
        self.assertIn("Search first and inspect large sources through focused ranges", reference)
        self.assertIn("fully ingest every source needed for an exact transformation", reference)
        self.assertIn("Probe the runtime, tools, packages, and services", reference)
        self.assertIn("When the required checks pass", reference)
        self.assertNotIn("normally at least 30 seconds", reference)

    def test_mature_instruction_fixture_passes_contract_validation(self):
        result = validate_target_repo.validate_repo(FIXTURES / "mature_repo", mode="read-only")
        self.assertTrue(result["success"], result)

    def test_contract_v3_target_validator_enforces_managed_instruction_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(FIXTURES / "mature_repo", root, dirs_exist_ok=True)
            engineering_index = root / "docs/engineering/README.md"
            engineering_index.write_text(
                "# Engineering Documentation Index\n\n"
                f"{common.INDEX_MARKER_START}\n"
                "No indexed documents yet.\n"
                f"{common.INDEX_MARKER_END}\n",
                encoding="utf-8",
            )

            result = validate_target_repo.validate_repo(root, mode="read-only")

            self.assertFalse(result["success"], result)
            self.assertTrue(
                any(
                    "Archive index error: index_entry_mismatch in docs/engineering/README.md" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_compileall_is_not_read_only_safe(self):
        self.assertEqual(common.classify_command_safety("python -m compileall ."), "copy_only_safe")

    def test_git_diff_check_is_read_only_safe(self):
        self.assertEqual(common.classify_command_safety("git diff --check"), "read_only_safe")

    def test_safe_git_inspection_matrix(self):
        for command in ("git status --short", "git diff", "git diff --check", "git ls-files"):
            with self.subTest(command=command):
                self.assertEqual(common.classify_command_safety(command), "read_only_safe")

    def test_git_helper_execution_options_are_live_only(self):
        commands = (
            "git grep --open-files-in-pager=malicious pattern",
            "git grep -Omalicious pattern",
            "git diff --ext-diff",
            "git show --textconv HEAD:file.txt",
            "git --paginate status",
            "git -c core.pager=malicious diff",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(common.classify_command_safety(command), "live_only")

    def test_find_output_actions_are_live_only(self):
        for action in ("-fprint", "-fprint0", "-fprintf", "-fls"):
            command = f"find . {action} output.txt"
            with self.subTest(command=command):
                self.assertEqual(common.classify_command_safety(command), "live_only")

    def test_repo_authored_and_package_commands_are_copy_only(self):
        for command in (
            "make help",
            "python repo_script.py --help",
            "python -m unittest",
            "pytest -q",
            "npm test",
        ):
            with self.subTest(command=command):
                self.assertEqual(common.classify_command_safety(command), "copy_only_safe")

    def test_shell_control_and_destructive_commands_are_live_only(self):
        commands = (
            "git status --short | head",
            "git status --short > report.txt",
            "git status --short && rm -rf build",
            "git diff --check; touch result",
            "git status $(touch result)",
            "git status `touch result`",
            "rm -rf build",
            "git status --short || git clean -fd",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(common.classify_command_safety(command), "live_only")

    def test_sed_allows_bounded_read_but_not_write_mode(self):
        self.assertEqual(common.classify_command_safety("sed -n '1,5p' README.md"), "read_only_safe")
        self.assertEqual(common.classify_command_safety("sed -n 'w output.txt' README.md"), "live_only")
        self.assertEqual(common.classify_command_safety("sed -n '1w output.txt' README.md"), "live_only")
        self.assertEqual(common.classify_command_safety("sed -n '1e touch-output' README.md"), "live_only")

    def test_sensitive_output_is_separate_from_read_only_tool_name(self):
        risks = common.classify_command_risks("cat .env")
        self.assertTrue(risks["sensitive_output"])
        self.assertEqual(risks["classification"], "live_only")
        self.assertEqual(common.classify_command_safety("test -e .env"), "read_only_safe")
        self.assertEqual(common.classify_command_safety("rg --files .env"), "read_only_safe")

    def test_read_only_mode_rejects_compileall(self):
        result = validate_target_repo.validate_repo(
            FIXTURES / "minimal_git_repo",
            mode="read-only",
            check_commands=["python -m compileall ."],
        )
        self.assertFalse(result["success"])
        self.assertTrue(result["errors"])

    def test_disposable_copy_runs_without_mutating_source(self):
        source = FIXTURES / "minimal_git_repo"
        result = validate_target_repo.validate_repo(
            source,
            mode="copy",
            check_commands=["python -m compileall ."],
            run_commands=["python -m compileall ."],
        )
        self.assertTrue(result["success"], result)
        self.assertFalse(any(path.name == "__pycache__" for path in source.rglob("*")))

    def test_exact_compileall_uses_isolated_stdlib_module_without_os_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "repo"
            source.mkdir()
            outside = base / "outside.txt"
            (source / "compileall.py").write_text(
                "from pathlib import Path\n" + f"Path({str(outside)!r}).write_text('unexpected')\n",
                encoding="utf-8",
            )
            with mock.patch.object(common, "_network_guard_prefix", return_value=None):
                results = common.run_in_disposable_copy(source, ["python -m compileall ."])
            self.assertEqual(results[0]["status"], "passed", results)
            self.assertFalse(outside.exists())

    def test_altered_compileall_is_not_exempt_without_os_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "repo"
            (source / "src").mkdir(parents=True)
            (source / "src" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            with mock.patch.object(common, "_network_guard_prefix", return_value=None):
                results = common.run_in_disposable_copy(source, ["python -m compileall ./src"])
            self.assertEqual(results[0]["status"], "rejected")
            self.assertIn("network isolation", results[0]["reason"])

    def test_network_capable_package_command_is_rejected_in_copy(self):
        result = validate_target_repo.validate_repo(
            FIXTURES / "minimal_git_repo",
            mode="copy",
            run_commands=["npm test"],
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["disposable_results"][0]["status"], "rejected")

    def test_disposable_copy_rejects_external_symlink(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "repo"
            source.mkdir()
            outside = base / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            (source / "linked.txt").symlink_to(Path("..") / outside.name)
            results = common.run_in_disposable_copy(source, ["python -m compileall ."])
            self.assertEqual(results[0]["status"], "rejected")
            self.assertIn("external symlink", results[0]["reason"])

    def test_disposable_runner_cannot_write_outside_its_temporary_root(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "repo"
            source.mkdir()
            outside = base / "outside.txt"
            script = source / "write_probe.py"
            script.write_text(
                "from pathlib import Path\n" + f"Path({str(outside)!r}).write_text('unexpected')\n",
                encoding="utf-8",
            )
            results = common.run_in_disposable_copy(source, ["python write_probe.py"])
            self.assertNotEqual(results[0]["status"], "passed")
            self.assertFalse(outside.exists())

    def test_disposable_runner_denies_network_or_refuses_unisolated_repo_code(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "repo"
            source.mkdir()
            (source / "network_probe.py").write_text(
                "import socket\nsock = socket.socket()\nsock.bind(('127.0.0.1', 0))\n",
                encoding="utf-8",
            )
            results = common.run_in_disposable_copy(source, ["python network_probe.py"])
            self.assertNotEqual(results[0]["status"], "passed")

    def test_validation_results_never_echo_secret_bearing_commands(self):
        marker = "SYNTHETIC_" + "COMMAND_SECRET_90123"
        check_command = "rm -- " + marker
        run_command = "python -c " + repr("print(" + marker + ")")
        result = validate_target_repo.validate_repo(
            FIXTURES / "minimal_git_repo",
            mode="copy",
            check_commands=[check_command],
            run_commands=[run_command],
        )
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn(marker, serialized)
        self.assertIn("command_fingerprint", serialized)
        self.assertIn("validation-command-", serialized)

    def test_validation_warns_on_prompt_injection_signals(self):
        result = validate_target_repo.validate_repo(FIXTURES / "suspicious_repo", mode="read-only")
        self.assertTrue(result["success"])
        self.assertTrue(result["prompt_injection_risks"])
        self.assertTrue(any("Suspicious agent-directed instructions" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
