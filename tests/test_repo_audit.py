from __future__ import annotations

import shutil
import tempfile
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
        self.assertTrue(result["instruction_contract"]["success"], result["instruction_contract"])
        self.assertIn("archive_indexes", result)
        self.assertIn("docs/README.md", result["ownership"]["managed"])

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

    def test_unknown_docs_under_workflow_directories_are_not_managed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(FIXTURES / "mature_repo", root, dirs_exist_ok=True)
            codex_doc = root / "docs" / "codex" / "team-notes.md"
            engineering_doc = root / "docs" / "engineering" / "service-notes.md"
            codex_doc.parent.mkdir(parents=True, exist_ok=True)
            engineering_doc.parent.mkdir(parents=True, exist_ok=True)
            codex_doc.write_text("repository context", encoding="utf-8")
            engineering_doc.write_text("repository context", encoding="utf-8")
            result = repo_audit.audit_repo(root)
            self.assertIn("docs/codex/team-notes.md", result["ownership"]["unknown"])
            self.assertIn("docs/engineering/service-notes.md", result["ownership"]["unknown"])
            self.assertNotIn("docs/codex/team-notes.md", result["ownership"]["managed"])
            self.assertNotIn("docs/engineering/service-notes.md", result["ownership"]["managed"])

    def test_manifest_manages_only_exact_declared_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            managed = root / "docs" / "codex" / "owned.md"
            unknown = root / "docs" / "codex" / "other.md"
            manifest = root / "docs" / "codex" / "ENGINEERING_WORKFLOW_STATE.yaml"
            managed.parent.mkdir(parents=True)
            managed.write_text("owned", encoding="utf-8")
            unknown.write_text("unknown", encoding="utf-8")
            manifest.write_text("managed_paths:\n  - docs/codex/owned.md\n", encoding="utf-8")
            result = repo_audit.audit_repo(root)
            self.assertIn("docs/codex/owned.md", result["ownership"]["managed"])
            self.assertIn("docs/codex/other.md", result["ownership"]["unknown"])


if __name__ == "__main__":
    unittest.main()
