from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module

FIXTURES = Path(__file__).resolve().parent / "fixtures"
common = load_script_module("common")
repo_audit = load_script_module("repo_audit")


class RepoAuditTests(unittest.TestCase):
    def _init_git_repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q", str(root)], check=True)

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

    def test_git_inventory_excludes_ignored_untracked_and_keeps_tracked_and_untracked_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._init_git_repo(root)
            (root / ".gitignore").write_text(".quality-logs/\nAGENTS.md\n", encoding="utf-8")
            (root / "README.md").write_text("overview", encoding="utf-8")
            (root / "AGENTS.md").write_text("explicit canonical owner", encoding="utf-8")
            ignored = root / ".quality-logs" / "py312" / "venv" / "lib" / "site-packages"
            ignored.mkdir(parents=True)
            (ignored / "entry_points.txt").write_text("synthetic entry point", encoding="utf-8")
            tracked_ignored = root / ".quality-logs" / "tracked-policy.md"
            tracked_ignored.write_text("tracked policy", encoding="utf-8")
            untracked_doc = root / "docs" / "untracked-notes.md"
            unusual_doc = root / "docs" / "line\nbreak.md"
            untracked_doc.parent.mkdir()
            untracked_doc.write_text("untracked context", encoding="utf-8")
            unusual_doc.write_text("tracked unusual context", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", ".gitignore", "README.md", "docs/line\nbreak.md"],
                check=True,
            )
            subprocess.run(["git", "-C", str(root), "add", "-f", ".quality-logs/tracked-policy.md"], check=True)

            result = repo_audit.audit_repo(root)
            paths = {item["path"] for item in result["workflow_artifacts"]}

            self.assertEqual(result["discovery"]["mode"], "git")
            self.assertNotIn(".quality-logs/py312/venv/lib/python3.12/site-packages/entry_points.txt", paths)
            self.assertIn(".quality-logs/tracked-policy.md", paths)
            self.assertIn("AGENTS.md", paths)
            self.assertIn("docs/untracked-notes.md", paths)
            self.assertIn("docs/line\nbreak.md", paths)

    def test_broken_git_inventory_uses_reported_bounded_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / "README.md").write_text("overview", encoding="utf-8")

            files, discovery = common.discover_audit_files(root)

            self.assertIn(root / "README.md", files)
            self.assertEqual(discovery["mode"], "bounded_filesystem")
            self.assertEqual(discovery["fallback_reason"], "git_inventory_failed")
            self.assertIn("git_inventory_failed", discovery["omission_reasons"])

    def test_non_git_fallback_is_bounded_prunes_generated_trees_and_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as external_tmp:
            root = Path(tmp)
            external = Path(external_tmp)
            (root / "README.md").write_text("overview", encoding="utf-8")
            generated = root / ".venv" / "lib" / "site-packages"
            generated.mkdir(parents=True)
            for index in range(20):
                (generated / f"generated-{index}.txt").write_text("generated", encoding="utf-8")
            (external / "outside.md").write_text("outside", encoding="utf-8")
            (root / "linked-docs").symlink_to(external, target_is_directory=True)
            (root / "docs").mkdir()
            (root / "docs" / "visible.md").write_text("visible", encoding="utf-8")

            with mock.patch.object(common, "AUDIT_FALLBACK_MAX_ENTRIES", 4):
                files, discovery = common.discover_audit_files(root)

            relative = {path.relative_to(root).as_posix() for path in files}
            self.assertEqual(discovery["mode"], "bounded_filesystem")
            self.assertNotIn(".venv/lib/site-packages/generated-0.txt", relative)
            self.assertNotIn("linked-docs/outside.md", relative)
            self.assertIn("README.md", relative)
            self.assertLessEqual(discovery["candidate_count"], 5)
            self.assertTrue(discovery["truncated"])
            self.assertIn("entry_limit", discovery["omission_reasons"])

    def test_compact_summary_writes_complete_report_and_preserves_failure_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "audit.json"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = repo_audit.main(
                    [str(FIXTURES / "suspicious_repo"), "--summary", "--full-report", str(report_path)]
                )

            summary = json.loads(stdout.getvalue())
            complete = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(summary["status"], "attention_required")
            self.assertIn("prompt_injection_risks", summary["failure_categories"])
            self.assertTrue(summary["omissions"]["details_omitted"])
            self.assertIn("root", summary["omissions"]["full_report_fields"])
            self.assertEqual(summary["full_report"]["path"], str(report_path))
            self.assertGreater(summary["full_report"]["size_bytes"], 0)
            self.assertTrue(complete["prompt_injection_risks"])
            self.assertIn("context_docs", complete)

    def test_default_cli_output_remains_complete_json(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = repo_audit.main([str(FIXTURES / "general_repo")])

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertIn("root", report)
        self.assertIn("context_docs", report)
        self.assertIn("workflow_artifacts", report)
        self.assertNotIn("full_report", report)


if __name__ == "__main__":
    unittest.main()
