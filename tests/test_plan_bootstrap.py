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
        actions = {item["path"]: item["action"] for item in result["artifact_actions"]}
        self.assertEqual(actions["AGENTS.md"], "create")

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
