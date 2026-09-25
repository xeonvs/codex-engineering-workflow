from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module
from test_upgrade_target_workflow import make_target, snapshot

common = load_script_module("common")
migrator = load_script_module("upgrade_target_workflow")

CLAUDE_NAMES = ("workflow-utility", "workflow-explorer", "workflow-reviewer")


class ClaudeAgentUpgradeTests(unittest.TestCase):
    def test_codex_opt_in_does_not_install_claude_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            settings = root / ".claude/settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text('{"model":"team-owned"}\n', encoding="utf-8")

            result = migrator.apply_migration(root, "0.9.10", include_agent_config=True)

            self.assertTrue(result["success"], result)
            self.assertFalse(result["include_claude_agent_config"])
            self.assertFalse((root / ".claude/agents").exists())
            self.assertEqual(settings.read_text(encoding="utf-8"), '{"model":"team-owned"}\n')

    def test_separate_claude_opt_in_creates_only_native_agents_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            report = migrator.build_migration_report(root, "0.9.10", include_claude_agent_config=True)
            self.assertTrue(report["success"], report)
            self.assertTrue(report["include_claude_agent_config"])
            self.assertFalse(report["include_agent_config"])
            self.assertFalse((root / "PLANS.md").exists())

            result = migrator.apply_migration(root, "0.9.10", include_claude_agent_config=True)
            self.assertTrue(result["success"], result)
            self.assertFalse((root / ".codex").exists())
            for name in CLAUDE_NAMES:
                path = root / ".claude/agents" / f"{name}.md"
                self.assertTrue(path.is_file(), name)
                self.assertEqual(
                    path.read_bytes(),
                    (migrator.CLAUDE_AGENT_TEMPLATE_ROOT / f"{name}.md.tmpl").read_bytes(),
                )
            state = (root / common.STATE_MANIFEST_PATH).read_text(encoding="utf-8")
            self.assertIn("runtime_claude_agent_config_managed: true", state)
            self.assertIn('".claude/agents/workflow-reviewer.md"', state)
            self.assertIn("runtime_agent_config_managed: false", state)
            before = snapshot(root)

            current = migrator.execute_prompt_upgrade(root, "0.9.10")
            self.assertTrue(current["success"], current)
            self.assertTrue(current["include_claude_agent_config"])
            self.assertEqual(current["update_status"], "already_current")
            self.assertEqual(current["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

    def test_claude_opt_in_preserves_user_pins_and_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            reviewer = root / ".claude/agents/workflow-reviewer.md"
            reviewer.parent.mkdir(parents=True)
            pinned = (
                "---\nname: workflow-reviewer\ndescription: Team reviewer\nmodel: inherit\n---\nTeam-owned guidance.\n"
            )
            reviewer.write_text(pinned, encoding="utf-8")
            settings = root / ".claude/settings.json"
            settings.write_text('{"model":"team-owned","effortLevel":"high"}\n', encoding="utf-8")
            claude_md = root / "CLAUDE.md"
            claude_md.write_text("# Team instructions\n", encoding="utf-8")

            result = migrator.apply_migration(root, "0.9.10", include_claude_agent_config=True)

            self.assertTrue(result["success"], result)
            self.assertEqual(reviewer.read_text(encoding="utf-8"), pinned)
            self.assertEqual(settings.read_text(encoding="utf-8"), '{"model":"team-owned","effortLevel":"high"}\n')
            self.assertEqual(claude_md.read_text(encoding="utf-8"), "# Team instructions\n")
            self.assertFalse((root / ".codex").exists())

    def test_claude_opt_in_preserves_existing_empty_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            utility = root / ".claude/agents/workflow-utility.md"
            utility.parent.mkdir(parents=True)
            utility.write_bytes(b"")

            report = migrator.build_migration_report(root, "0.9.10", include_claude_agent_config=True)
            self.assertTrue(report["success"], report)
            proposed = {change["path"] for change in report["proposed_changes"]}
            self.assertNotIn(".claude/agents/workflow-utility.md", proposed)

            result = migrator.apply_migration(root, "0.9.10", include_claude_agent_config=True)
            self.assertTrue(result["success"], result)
            self.assertEqual(utility.read_bytes(), b"")
            self.assertNotIn(".claude/agents/workflow-utility.md", result["mutation_log"])

    def test_pristine_prior_template_refreshes_but_customized_agent_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            initial = migrator.apply_migration(root, "0.9.10", include_claude_agent_config=True)
            self.assertTrue(initial["success"], initial)
            reviewer = root / ".claude/agents/workflow-reviewer.md"
            utility = root / ".claude/agents/workflow-utility.md"
            prior = reviewer.read_text(encoding="utf-8").replace("model: sonnet", "model: inherit")
            self.assertNotEqual(prior, reviewer.read_text(encoding="utf-8"))
            reviewer.write_text(prior, encoding="utf-8")
            custom = utility.read_text(encoding="utf-8").replace("model: haiku", "model: inherit")
            utility.write_text(custom, encoding="utf-8")
            old_hash = hashlib.sha256(prior.encode("utf-8")).hexdigest()
            with mock.patch.dict(migrator.PRIOR_CLAUDE_AGENT_TEMPLATE_HASHES, {"workflow-reviewer": {old_hash}}):
                report = migrator.build_migration_report(root, "0.9.11")
                self.assertTrue(report["include_claude_agent_config"])
                updates = {change["path"] for change in report["proposed_changes"] if change["action"] == "update"}
                self.assertIn(".claude/agents/workflow-reviewer.md", updates)
                self.assertNotIn(".claude/agents/workflow-utility.md", updates)
                result = migrator.apply_migration(root, "0.9.11")
            self.assertTrue(result["success"], result)
            self.assertEqual(
                reviewer.read_bytes(), (migrator.CLAUDE_AGENT_TEMPLATE_ROOT / "workflow-reviewer.md.tmpl").read_bytes()
            )
            self.assertEqual(utility.read_text(encoding="utf-8"), custom)

    def test_unsafe_claude_agent_path_blocks_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            native = root / "native.md"
            native.write_text("# Native\n", encoding="utf-8")
            agent = root / ".claude/agents/workflow-utility.md"
            agent.parent.mkdir(parents=True)
            agent.symlink_to("../../native.md")

            report = migrator.build_migration_report(root, "0.9.10", include_claude_agent_config=True)
            self.assertFalse(report["success"], report)
            self.assertIn("canonical_symlink", {item["type"] for item in report["conflicts"]})
            result = migrator.apply_migration(root, "0.9.10", include_claude_agent_config=True)
            self.assertFalse(result["success"])
            self.assertEqual(result["mutation_log"], [])
            self.assertFalse((root / "PLANS.md").exists())
            self.assertTrue(agent.is_symlink())

    def test_claude_agent_creation_rolls_back_on_later_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            with mock.patch.object(migrator, "_manifest_text", side_effect=RuntimeError("synthetic failure")):
                result = migrator.apply_migration(root, "0.9.10", include_claude_agent_config=True)
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "rolled_back")
            self.assertFalse((root / ".claude").exists())
            self.assertFalse((root / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
