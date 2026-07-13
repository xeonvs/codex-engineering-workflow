from __future__ import annotations

import unittest
from pathlib import Path

from test_support import load_script_module


FIXTURES = Path(__file__).resolve().parent / "fixtures"
plan_bootstrap = load_script_module("plan_bootstrap")


class PlanBootstrapTests(unittest.TestCase):
    def test_empty_repo_defaults_to_greenfield(self):
        result = plan_bootstrap.build_plan(FIXTURES / "empty_directory")
        self.assertEqual(result["recommended_mode"], "greenfield_scaffold")
        self.assertTrue(result["requires_full_plan"])
        self.assertEqual(result["plan_schema_version"], 1)
        self.assertEqual(result["plan_origin"], "direct_execution")
        self.assertEqual(result["first_repository_write"], "PLANS.md")
        self.assertEqual(result["artifact_actions"][0]["path"], "PLANS.md")
        actions = {item["path"]: item["action"] for item in result["artifact_actions"]}
        self.assertEqual(actions["AGENTS.md"], "create")

    def test_read_only_workflow_requires_no_plan_or_writes(self):
        result = plan_bootstrap.build_plan(FIXTURES / "minimal_git_repo", repo_changing=False)
        self.assertEqual(result["recommended_mode"], "read_only_verify")
        self.assertFalse(result["requires_full_plan"])
        self.assertIsNone(result["plan_schema_version"])
        self.assertIsNone(result["plan_origin"])
        self.assertIsNone(result["first_repository_write"])
        self.assertEqual(result["artifact_actions"], [])

    def test_plan_mode_origin_does_not_change_full_plan_gate(self):
        result = plan_bootstrap.build_plan(
            FIXTURES / "minimal_git_repo",
            plan_origin="plan_mode_approved",
        )
        self.assertTrue(result["requires_full_plan"])
        self.assertEqual(result["plan_origin"], "plan_mode_approved")
        self.assertEqual(result["first_repository_write"], "PLANS.md")

    def test_invalid_plan_origin_is_rejected(self):
        with self.assertRaises(ValueError):
            plan_bootstrap.build_plan(FIXTURES / "minimal_git_repo", plan_origin="chat_summary")

    def test_mature_repo_requests_migration_note(self):
        result = plan_bootstrap.build_plan(FIXTURES / "mature_repo")
        optionals = {item["path"] for item in result["optional_artifact_actions"]}
        self.assertIn("docs/codex/exec_plan_migration_note.md", optionals)
        self.assertIn("retained_history_policy", result["questions"])

    def test_general_repo_preserves_existing_context_docs(self):
        result = plan_bootstrap.build_plan(FIXTURES / "general_repo")
        self.assertNotIn("content_footprint", result)
        protected_paths = {item["path"] for item in result["protected_doc_actions"]}
        self.assertIn("README.md", protected_paths)
        self.assertIn("docs/reference/deployment-notes.md", protected_paths)
        self.assertTrue(any("reference them from AGENTS.md" in note for note in result["notes"]))


if __name__ == "__main__":
    unittest.main()
