from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module
from test_update_installed_skill import init_upstream

adoption = load_script_module("release_adoption")
updates = load_script_module("workflow_updates")


class ReleaseAdoptionTests(unittest.TestCase):
    def test_future_release_without_descriptor_cannot_claim_complete_adoption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pending = adoption.assess_target_adoption(root, "0.10.0")["pending_change_ids"]
            report = adoption.assess_target_adoption(root, "0.11.0", pending)
            self.assertFalse(report["descriptor_covers_target"])
            self.assertEqual(report["adoption_status"], "pending")

    def test_skipped_releases_accumulate_capabilities(self):
        descriptor = {
            "schema_version": 1,
            "skill_version": "0.12.0",
            "changes": [
                {
                    "id": "first",
                    "introduced_in": "0.10.0",
                    "adoption_requirement": "semantic_review",
                    "affected_owner_patterns": ["AGENTS.md"],
                },
                {
                    "id": "second",
                    "introduced_in": "0.11.0",
                    "adoption_requirement": "runtime_only",
                    "affected_owner_patterns": [],
                },
            ],
        }
        self.assertEqual(
            [item["id"] for item in adoption.applicable_adoption_changes("0.9.10", descriptor)], ["first", "second"]
        )
        self.assertEqual(
            [item["id"] for item in adoption.applicable_adoption_changes("0.10.0", descriptor)], ["second"]
        )

    def test_same_version_stamp_never_resolves_semantic_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / adoption.STATE_PATH
            state.parent.mkdir(parents=True)
            state.write_text('skill_version: "0.10.0"\n')
            report = adoption.assess_target_adoption(root, "0.10.0")
            self.assertEqual(len(report["pending_change_ids"]), 4)
            resolved = adoption.assess_target_adoption(root, "0.10.0", report["pending_change_ids"])
            self.assertEqual(resolved["adoption_status"], "resolved")
            self.assertFalse(resolved["semantic_review_performed"])

    def test_discovery_does_not_follow_symbolic_document_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, outside = Path(tmp) / "target", Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "README.md").write_text("private content")
            (root / "docs").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                adoption.assess_target_adoption(root, "0.10.0")


class WorkflowUpdateTests(unittest.TestCase):
    def test_unverified_native_write_does_not_restore_old_cache_as_active_version(self):
        available = {**self.result, "skill_content_changed": True, "automatic_update_allowed": True}
        failed = {
            **self.result,
            "success": False,
            "currentness": "unknown",
            "update_status": "native_update_failed",
            "native_mutation_attempted": True,
            "native_readback_verified": False,
            "installed_version": None,
            "observed_native_version": None,
            "active_installation_path": None,
        }
        with (
            mock.patch.object(updates, "update_installation", side_effect=[available, failed]),
            mock.patch.object(
                updates,
                "assess_target_adoption",
                side_effect=AssertionError("Unverified native bytes cannot drive adoption"),
            ),
        ):
            result = updates.check_workflow_updates(
                self.target,
                self.install,
                state_path=self.state,
                apply=True,
                set_policy="automatic_stable",
                platform="codex",
            )
        self.assertFalse(result["success"])
        self.assertIsNone(result["installed_version"])
        self.assertEqual(result["last_known_installed_version"], "0.10.0")
        self.assertEqual(result["target_recommendation"]["adoption_status"], "native_readback_required")
        self.assertFalse(result["target_recommendation"]["proposal_emitted"])
        self.assertNotIn("check", json.loads(self.state.read_text()))

    def test_source_maintainer_repository_does_not_load_donor_instructions_as_target(self):
        source_skill = self.target / "skill/engineering-workflow/SKILL.md"
        source_skill.parent.mkdir(parents=True)
        source_skill.write_text("Source runtime owner\n")
        builder = self.target / "scripts/build_marketplace_package.py"
        builder.parent.mkdir()
        builder.write_text("# Source maintainer tool\n")
        with (
            mock.patch.object(updates, "update_installation", return_value=self.result),
            mock.patch.object(
                updates,
                "assess_target_adoption",
                side_effect=AssertionError("Source instructions must remain maintainer-owned"),
            ),
        ):
            result = updates.check_workflow_updates(self.target, self.install, state_path=self.state)
        self.assertEqual(result["target_recommendation"]["adoption_status"], "source_maintainer_review")
        self.assertFalse(result["target_recommendation"]["proposal_emitted"])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        source = init_upstream(self.root, "0.10.0")
        self.install = self.root / "installed"
        shutil.copytree(source / "skill" / "engineering-workflow", self.install)
        self.target = self.root / "target"
        self.target.mkdir()
        (self.target / "AGENTS.md").write_text("Customized local instructions remain unchanged\n")
        self.state = self.root / "state" / "installation.json"
        self.result = {
            "success": True,
            "update_status": "up_to_date",
            "currentness": "checked",
            "previous_version": "0.10.0",
            "candidate_version": "0.10.0",
            "source_ref": "v0.10.0",
            "resolved_commit": "a" * 40,
            "automatic_update_allowed": False,
            "skill_content_changed": False,
            "recommended_action": "refresh_loaded_skill",
            "private_unknown_value": "never persist this",
        }

    def tearDown(self):
        self.temporary.cleanup()

    def check(self, **kwargs):
        return updates.check_workflow_updates(self.target, self.install, state_path=self.state, **kwargs)

    def test_legacy_notify_cache_and_force_preserve_target(self):
        before = (self.target / "AGENTS.md").read_bytes()
        with mock.patch.object(updates, "update_installation", return_value=self.result) as updater:
            first = self.check(now=100000)
            second = self.check(now=100001)
            third = self.check(now=100002, force_check=True)
            self.assertEqual(updater.call_count, 2)
        self.assertEqual(first["installation_policy"], "notify_only")
        self.assertFalse(first["update_attempted"])
        self.assertTrue(second["check_cache_used"])
        self.assertFalse(third["check_cache_used"])
        self.assertEqual(before, (self.target / "AGENTS.md").read_bytes())
        serialized = self.state.read_text()
        self.assertNotIn("Customized local", serialized)
        self.assertNotIn(str(self.target), serialized)
        self.assertNotIn("never persist", serialized)

    def test_expired_cache_rechecks(self):
        with mock.patch.object(updates, "update_installation", return_value=self.result) as updater:
            self.check(now=100000)
            report = self.check(now=100000 + updates.CHECK_TTL_SECONDS)
        self.assertEqual(updater.call_count, 2)
        self.assertFalse(report["check_cache_used"])

    def test_failed_check_is_not_cached_and_network_recovery_rechecks(self):
        unavailable = {"success": False, "currentness": "unknown", "update_status": "upstream_unavailable"}
        with mock.patch.object(updates, "update_installation", side_effect=[unavailable, self.result]) as updater:
            first = self.check(now=100000)
            recovered = self.check(now=100001)
        self.assertFalse(first["check_cache_used"])
        self.assertFalse(recovered["check_cache_used"])
        self.assertTrue(recovered["success"])
        self.assertEqual(updater.call_count, 2)

    def test_successful_cache_does_not_hide_same_version_local_byte_drift(self):
        with mock.patch.object(updates, "update_installation", return_value=self.result) as updater:
            self.check(now=100000)
            (self.install / "references" / "policy.md").write_text("locally modified\n")
            report = self.check(now=100001)
        self.assertFalse(report["check_cache_used"])
        self.assertEqual(updater.call_count, 2)

    def test_declined_and_unchanged_proposals_suppress_until_candidate_changes_or_explicit(self):
        with mock.patch.object(updates, "update_installation", return_value=self.result):
            first = self.check(now=100000)
            updates.record_proposal_outcome(self.state, self.target, self.install, "declined")
            second = self.check(now=100001)
            explicit = self.check(now=100002, explicit_proposal=True)
            changed_result = self.result | {"resolved_commit": "b" * 40}
            with mock.patch.object(updates, "update_installation", return_value=changed_result):
                changed = self.check(now=100003, force_check=True)
        self.assertTrue(first["target_recommendation"]["proposal_emitted"])
        self.assertTrue(second["target_recommendation"]["proposal_suppressed"])
        self.assertEqual(second["target_recommendation"]["previous_outcome"], "declined")
        self.assertTrue(explicit["target_recommendation"]["proposal_emitted"])
        self.assertTrue(changed["target_recommendation"]["proposal_emitted"])

    def test_automatic_policy_is_explicit_and_pins_apply(self):
        available = self.result | {
            "skill_content_changed": True,
            "automatic_update_allowed": True,
            "update_status": "update_available",
        }
        applied = available | {"update_status": "updated", "installed_version": "0.10.0"}
        with mock.patch.object(updates, "update_installation", side_effect=[available, applied]) as updater:
            report = self.check(now=100000, set_policy="automatic_stable", apply=True)
        self.assertTrue(report["update_attempted"])
        self.assertEqual(updater.call_args.kwargs["expected_commit"], "a" * 40)
        with mock.patch.object(updates, "update_installation", return_value=available) as updater:
            report = self.check(now=100001, set_policy="notify_only", apply=True, force_check=True)
        self.assertFalse(report["update_attempted"])
        self.assertEqual(updater.call_count, 1)

    def test_notify_only_proposes_deliverable_before_install(self):
        available = self.result | {"candidate_version": "0.11.0", "update_status": "update_available"}
        with mock.patch.object(updates, "update_installation", return_value=available):
            report = self.check(now=100000)
        self.assertEqual(report["target_recommendation"]["target_version"], "0.11.0")
        self.assertTrue(report["target_recommendation"]["installation_update_required"])

    def test_offline_continues_installed_content_and_never_applies(self):
        unavailable = {"success": False, "currentness": "unknown", "update_status": "upstream_unavailable"}
        with mock.patch.object(updates, "update_installation", return_value=unavailable) as updater:
            report = self.check(now=100000, set_policy="automatic_stable", apply=True)
        self.assertFalse(report["success"])
        self.assertFalse(report["update_attempted"])
        self.assertEqual(updater.call_count, 1)
        self.assertEqual(report["installed_version"], "0.10.0")

    def test_state_cannot_be_written_into_target_or_installation(self):
        for owner in (self.target, self.install):
            with self.assertRaises(ValueError):
                updates.check_workflow_updates(self.target, self.install, state_path=owner / "policy.json")
        self.assertFalse((self.target / "policy.json").exists())

    def test_explicit_update_bypasses_check_cache(self):
        with mock.patch.object(updates, "update_installation", return_value=self.result) as updater:
            self.check(now=100000)
            report = self.check(now=100001, apply=True, explicit_update=True)
        self.assertEqual(updater.call_count, 2)
        self.assertFalse(report["check_cache_used"])

    def test_policy_identity_survives_versioned_plugin_cache_path(self):
        paths = []
        for version in ("0.10.0", "0.11.0"):
            bundle = self.root / "cache" / "engineering-workflow" / version
            skill = bundle / "skills" / "engineering-workflow"
            shutil.copytree(self.install, skill)
            metadata = bundle / ".codex-plugin" / "plugin.json"
            metadata.parent.mkdir()
            metadata.write_text("{}")
            paths.append(skill)
        self.assertEqual(updates.default_state_path(paths[0]), updates.default_state_path(paths[1]))

    def test_offline_check_does_not_repeat_a_declined_unchanged_installed_candidate(self):
        with mock.patch.object(updates, "update_installation", return_value=self.result):
            self.check(now=100000)
        updates.record_proposal_outcome(self.state, self.target, self.install, "declined")
        unavailable = {"success": False, "currentness": "unknown", "update_status": "upstream_unavailable"}
        with mock.patch.object(updates, "update_installation", return_value=unavailable):
            report = self.check(now=100001, force_check=True)
        self.assertTrue(report["target_recommendation"]["proposal_suppressed"])

    def test_offline_previous_candidate_is_not_reused_after_owner_evidence_changes(self):
        with mock.patch.object(updates, "update_installation", return_value=self.result):
            self.check(now=100000)
        updates.record_proposal_outcome(self.state, self.target, self.install, "declined")
        (self.target / "AGENTS.md").write_text("Materially different local instructions\n")
        unavailable = {"success": False, "currentness": "unknown", "update_status": "upstream_unavailable"}
        with mock.patch.object(updates, "update_installation", return_value=unavailable):
            report = self.check(now=100001, force_check=True)
        self.assertTrue(report["target_recommendation"]["proposal_emitted"])
        self.assertFalse(report["target_recommendation"]["proposal_suppressed"])

    def test_cached_candidate_descriptor_retains_skipped_future_capabilities(self):
        descriptor = {
            "schema_version": 1,
            "skill_version": "0.11.0",
            "changes": [
                {
                    "id": "future-review",
                    "introduced_in": "0.11.0",
                    "summary": "Review the future owner contract.",
                    "adoption_requirement": "semantic_review",
                    "affected_owner_patterns": ["AGENTS.md"],
                }
            ],
        }
        available = self.result | {"candidate_version": "0.11.0", "release_adoption_descriptor": descriptor}
        with mock.patch.object(updates, "update_installation", return_value=available) as updater:
            first = self.check(now=100000)
            cached = self.check(now=100001)
        self.assertEqual(first["target_recommendation"]["pending_change_ids"], ["future-review"])
        self.assertEqual(cached["target_recommendation"]["pending_change_ids"], ["future-review"])
        self.assertEqual(cached["target_recommendation"]["changes"][0]["summary"], "Review the future owner contract.")
        self.assertTrue(cached["check_cache_used"])
        self.assertEqual(updater.call_count, 1)

    def test_cached_descriptor_rejects_unknown_fields(self):
        with mock.patch.object(updates, "update_installation", return_value=self.result):
            self.check(now=100000)
        state = json.loads(self.state.read_text())
        state["check"]["result"]["release_adoption_descriptor"] = {
            "schema_version": 1,
            "skill_version": "0.10.0",
            "changes": [
                {
                    "id": "documentation-navigation-v1",
                    "introduced_in": "0.10.0",
                    "summary": "Bounded summary.",
                    "adoption_requirement": "semantic_review",
                    "affected_owner_patterns": ["AGENTS.md"],
                    "unexpected": "do not persist",
                }
            ],
        }
        self.state.write_text(json.dumps(state))
        with self.assertRaises(ValueError):
            self.check(now=100001)

    def test_workflow_entrypoint_disables_bytecode_before_sibling_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp) / "runtime"
            scripts = runtime / "scripts"
            assets = runtime / "assets"
            scripts.mkdir(parents=True)
            assets.mkdir()
            source_scripts = Path(updates.__file__).resolve().parent
            for name in (
                "workflow_updates.py",
                "release_adoption.py",
                "update_installed_skill.py",
                "documentation_navigation.py",
                "common.py",
            ):
                shutil.copy2(source_scripts / name, scripts / name)
            shutil.copy2(
                Path(updates.__file__).resolve().parents[1] / "assets" / "release_adoption.json",
                assets / "release_adoption.json",
            )
            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            completed = subprocess.run(
                [sys.executable, str(scripts / "workflow_updates.py"), "--help"],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse(any(path.name == "__pycache__" for path in runtime.rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main()
