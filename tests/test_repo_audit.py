from __future__ import annotations

import unittest
from pathlib import Path

from test_support import load_script_module


FIXTURES = Path(__file__).resolve().parent / "fixtures"
repo_audit = load_script_module("repo_audit")


class RepoAuditTests(unittest.TestCase):
    def test_empty_directory_is_detected(self):
        result = repo_audit.audit_repo(FIXTURES / "empty_directory")
        self.assertEqual(result["repo_maturity"], "empty_directory")

    def test_minimal_repo_is_detected(self):
        result = repo_audit.audit_repo(FIXTURES / "minimal_git_repo")
        self.assertEqual(result["repo_maturity"], "minimal_repo")
        self.assertIn("python -m compileall .", result["recommended_validation"]["copy_only_safe"])

    def test_mature_repo_is_detected(self):
        result = repo_audit.audit_repo(FIXTURES / "mature_repo")
        self.assertEqual(result["repo_maturity"], "mature_repo")
        self.assertTrue(result["retained_history"])
        self.assertTrue(result["canonical_files"]["agents"])

    def test_general_repo_uses_structural_audit(self):
        result = repo_audit.audit_repo(FIXTURES / "general_repo")
        self.assertEqual(result["repo_maturity"], "mature_repo")
        self.assertNotIn("content_footprint", result)

        context_paths = {item["path"] for item in result["context_docs"]}
        self.assertIn("README.md", context_paths)
        self.assertIn("docs/reference/deployment-notes.md", context_paths)
        self.assertIn("qa/test-strategy.md", context_paths)

    def test_suspicious_repo_reports_prompt_injection_risks(self):
        result = repo_audit.audit_repo(FIXTURES / "suspicious_repo")
        self.assertTrue(result["prompt_injection_risks"])
        finding_types = {item["type"] for item in result["prompt_injection_risks"]}
        self.assertIn("instruction_override", finding_types)
        self.assertIn("remote_execution", finding_types)


if __name__ == "__main__":
    unittest.main()
