from __future__ import annotations

import unittest
from pathlib import Path

from test_support import load_script_module


FIXTURES = Path(__file__).resolve().parent / "fixtures"
common = load_script_module("common")
validate_target_repo = load_script_module("validate_target_repo")


class ValidationTests(unittest.TestCase):
    def test_compileall_is_not_read_only_safe(self):
        self.assertEqual(common.classify_command_safety("python -m compileall ."), "copy_only_safe")

    def test_git_diff_check_is_read_only_safe(self):
        self.assertEqual(common.classify_command_safety("git diff --check"), "read_only_safe")

    def test_read_only_mode_rejects_compileall(self):
        result = validate_target_repo.validate_repo(
            FIXTURES / "minimal_git_repo",
            mode="read-only",
            check_commands=["python -m compileall ."],
        )
        self.assertFalse(result["success"])
        self.assertTrue(result["errors"])

    def test_validation_warns_on_prompt_injection_signals(self):
        result = validate_target_repo.validate_repo(FIXTURES / "suspicious_repo", mode="read-only")
        self.assertTrue(result["success"])
        self.assertTrue(result["prompt_injection_risks"])
        self.assertTrue(any("Suspicious agent-directed instructions" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
