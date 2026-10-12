from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module
from test_upgrade_target_workflow import make_target, snapshot

migrator = load_script_module("upgrade_target_workflow")
adoption = load_script_module("release_adoption")


class ReleaseAdoptionUpgradeTests(unittest.TestCase):
    def test_generated_target_adopts_all_current_capabilities_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            result = migrator.execute_prompt_upgrade(root, "0.10.0")
            self.assertTrue(result["success"], result)
            state = (root / migrator.STATE_MANIFEST_PATH).read_text()
            for change in adoption.load_descriptor()["changes"]:
                self.assertIn(change["id"], state)
            before = snapshot(root)
            current = migrator.execute_prompt_upgrade(root, "0.10.0")
            self.assertEqual(current["update_status"], "already_current", current)
            self.assertEqual(snapshot(root), before)

    def test_customized_same_version_needs_review_before_recording_adoption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            initial = migrator.execute_prompt_upgrade(root, "0.9.10")
            self.assertTrue(initial["success"], initial)
            agents = root / "AGENTS.md"
            agents.write_text(agents.read_text() + "\nPreserved project-owned context.\n")
            state = root / migrator.STATE_MANIFEST_PATH
            state.write_text(state.read_text().replace('skill_version: "0.9.10"', 'skill_version: "0.10.0"'))
            before = snapshot(root)
            report = migrator.execute_prompt_upgrade(root, "0.10.0")
            self.assertEqual(report["agent_action"], "review_release_adoption", report)
            self.assertEqual(report["mutation_log"], [])
            self.assertTrue(report["instruction_contract"]["success"])
            self.assertEqual(snapshot(root), before)
            ids = report["release_adoption"]["pending_change_ids"]
            result = migrator.execute_prompt_upgrade(root, "0.10.0", reviewed_change_ids=ids)
            self.assertTrue(result["success"], result)
            self.assertEqual(agents.read_bytes(), before["AGENTS.md"])
            self.assertTrue(adoption.assess_target_adoption(root, "0.10.0")["adoption_status"] == "resolved")

    def test_custom_documentation_configuration_and_section_prose_survive_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            initial = migrator.apply_migration(root, "0.9.10")
            self.assertTrue(initial["success"], initial)
            manuals = root / "manuals"
            manuals.mkdir()
            (manuals / "policy.md").write_text("# Policy\n\nTeam-owned rules.\n")
            index = manuals / "README.md"
            index.write_text(
                "# Manuals\n\nOwner introduction.\n\n"
                "<!-- engineering-workflow:index:start -->\n"
                "<!-- engineering-workflow:index:end -->\n\nOwner conclusion.\n"
            )
            state = root / migrator.STATE_MANIFEST_PATH
            state.write_text(
                state.read_text().replace("managed_paths:\n", "managed_paths:\n  - manuals/README.md\n")
                + "documentation_roots:\n  - docs\n  - manuals\ndocumentation_indexes:\n  - manuals/README.md\n"
            )
            result = migrator.apply_migration(root, "0.10.0")
            self.assertTrue(result["success"], result)
            self.assertIn("Owner introduction.", index.read_text())
            self.assertIn("Owner conclusion.", index.read_text())
            self.assertIn("(policy.md)", index.read_text())
            self.assertIn("documentation_roots:", state.read_text())
            self.assertIn('"manuals"', state.read_text())
            self.assertIn('"manuals/README.md"', state.read_text())

    def test_recorded_adoption_does_not_hide_later_custom_owner_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            self.assertTrue(migrator.execute_prompt_upgrade(root, "0.10.0")["success"])
            agents = root / "AGENTS.md"
            agents.write_text(agents.read_text() + "\nLocal writing owner changed.\n")
            before = snapshot(root)
            result = migrator.execute_prompt_upgrade(root, "0.10.0")
            self.assertEqual(result["agent_action"], "review_release_adoption", result)
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual(snapshot(root), before)
            reviewed = migrator.execute_prompt_upgrade(
                root, "0.10.0", reviewed_change_ids=result["release_adoption"]["pending_change_ids"]
            )
            self.assertTrue(reviewed["success"], reviewed)
            self.assertEqual(migrator.execute_prompt_upgrade(root, "0.10.0")["update_status"], "already_current")

    def test_unknown_review_id_refuses_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            before = snapshot(root)
            with self.assertRaises(migrator.MigrationConflict) as caught:
                migrator.apply_migration(root, "0.10.0", reviewed_change_ids=["unknown-change"])
            self.assertEqual(caught.exception.code, "invalid_reviewed_change")
            self.assertEqual(snapshot(root), before)

    def test_pristine_root_does_not_auto_review_nested_instruction_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            self.assertTrue(migrator.execute_prompt_upgrade(root, "0.10.0")["success"])
            nested = root / "manuals/AGENTS.md"
            nested.parent.mkdir()
            nested.write_text("# Local documentation rules\n\nPreserve team writing conventions.\n")
            before = snapshot(root)
            result = migrator.execute_prompt_upgrade(root, "0.10.0")
            self.assertEqual(result["agent_action"], "review_release_adoption", result)
            self.assertEqual(result["release_adoption"]["template_change_ids"], [])
            self.assertEqual(snapshot(root), before)

    def test_reviewed_owner_drift_during_apply_is_not_stamped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            self.assertTrue(migrator.execute_prompt_upgrade(root, "0.9.10")["success"])
            agents = root / "AGENTS.md"
            agents.write_text(agents.read_text() + "\nLocal writing rules.\n")
            report = migrator.build_migration_report(root, "0.10.0")
            original = migrator.planned_index_writes

            def drift_after_report(target):
                agents.write_text(agents.read_text() + "\nUnreviewed concurrent rule.\n")
                return original(target)

            with mock.patch.object(migrator, "planned_index_writes", side_effect=drift_after_report):
                result = migrator.apply_migration(
                    root, "0.10.0", reviewed_change_ids=report["release_adoption"]["pending_change_ids"]
                )
            self.assertFalse(result["success"], result)
            self.assertEqual(result["update_status"], "rolled_back", result)
            self.assertIn("adoption_owner_changed", {item["code"] for item in result["errors"]})
            self.assertIn('skill_version: "0.9.10"', (root / migrator.STATE_MANIFEST_PATH).read_text())
            self.assertIn("Unreviewed concurrent rule.", agents.read_text())

    def test_source_identity_does_not_guess_release_from_requested_version(self):
        rendered = migrator._manifest_text("0.9.10", [], [], False)
        self.assertNotIn('source_ref: "0.9.10"', rendered)
        self.assertNotIn('source_ref: "v0.9.10"', rendered)


if __name__ == "__main__":
    unittest.main()
