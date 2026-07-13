from __future__ import annotations

import os
import shutil
import stat
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module


common = load_script_module("common")
migrator = load_script_module("upgrade_target_workflow")


def make_target(root: Path) -> None:
    (root / "README.md").write_text("# Target\n", encoding="utf-8")
    architecture = root / "docs" / "architecture" / "system.md"
    unknown_codex = root / "docs" / "codex" / "team-notes.md"
    unknown_engineering = root / "docs" / "engineering" / "service-notes.md"
    architecture.parent.mkdir(parents=True, exist_ok=True)
    unknown_codex.parent.mkdir(parents=True, exist_ok=True)
    unknown_engineering.parent.mkdir(parents=True, exist_ok=True)
    architecture.write_text("architecture owner\n", encoding="utf-8")
    unknown_codex.write_text("team context\n", encoding="utf-8")
    unknown_engineering.write_text("service context\n", encoding="utf-8")


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class UpgradeTargetWorkflowTests(unittest.TestCase):
    def test_plan_mode_is_fully_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            before = snapshot(root)
            result = migrator.build_migration_report(root, "0.5.0")
            self.assertTrue(result["success"], result)
            self.assertEqual(result["mode"], "plan")
            self.assertEqual(snapshot(root), before)
            self.assertFalse((root / "PLANS.md").exists())

    def test_invalid_target_version_is_refused_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            before = snapshot(root)

            with self.assertRaises(migrator.MigrationConflict) as error:
                migrator.build_migration_report(root, "0.5.1\n## injected")

            self.assertEqual(error.exception.code, "invalid_target_version")
            self.assertEqual(snapshot(root), before)

    def test_apply_creates_plan_first_and_writes_state_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            result = migrator.apply_migration(root, "0.5.0")
            self.assertTrue(result["success"], result)
            self.assertEqual(result["mutation_log"][0], "PLANS.md")
            self.assertTrue((root / "docs" / "codex" / "ENGINEERING_WORKFLOW_STATE.yaml").exists())
            plan_text = (root / "PLANS.md").read_text(encoding="utf-8")
            self.assertEqual(common.validate_plan_schema(plan_text, declared_external_sources=True), [])
            self.assertIn("Status: done", plan_text)

    def test_atomic_replacement_preserves_existing_file_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            plans = root / "PLANS.md"
            plans.write_text("# Execution Plans\n", encoding="utf-8")
            plans.chmod(0o600)

            result = migrator.apply_migration(root, "0.5.1")

            self.assertTrue(result["success"], result)
            self.assertEqual(stat.S_IMODE(plans.stat().st_mode), 0o600)

    def test_rollback_removes_directories_created_by_failed_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            root.mkdir(exist_ok=True)
            (root / "README.md").write_text("# Target\n", encoding="utf-8")
            with mock.patch.object(migrator, "_manifest_text", side_effect=RuntimeError("synthetic failure")):
                result = migrator.apply_migration(root, "0.5.1")

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "rolled_back")
            self.assertTrue((root / "PLANS.md").is_file())
            self.assertFalse((root / "AGENTS.md").exists())
            self.assertFalse((root / "docs").exists())

    def test_prompt_upgrade_runs_report_then_safe_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)

            result = migrator.execute_prompt_upgrade(root, "0.5.1")

            self.assertTrue(result["success"], result)
            self.assertEqual(result["mode"], "prompt")
            self.assertTrue(result["report_reviewed"])
            self.assertEqual(result["agent_action"], "complete_and_validate")
            self.assertEqual(result["mutation_log"][0], "PLANS.md")
            manifest = root / "docs" / "codex" / "ENGINEERING_WORKFLOW_STATE.yaml"
            self.assertIn('skill_version: "0.5.1"', manifest.read_text(encoding="utf-8"))

    def test_prompt_upgrade_asks_one_question_without_writes_on_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            plans = root / "PLANS.md"
            original = "# Plans\n\n## Active Plan: Product Release\n\nStatus: in_progress\n"
            plans.write_text(original, encoding="utf-8")

            result = migrator.execute_prompt_upgrade(root, "0.5.1")

            self.assertFalse(result["success"])
            self.assertEqual(result["mode"], "prompt")
            self.assertEqual(result["agent_action"], "ask_targeted_question")
            self.assertEqual(len(result["required_user_questions"]), 1)
            self.assertEqual(result["question_to_ask"], result["required_user_questions"][0])
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual(plans.read_text(encoding="utf-8"), original)

    def test_prompt_upgrade_stops_without_writes_on_privacy_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            private_path = "/" + "Users" + "/sample/private/project"
            readme = root / "README.md"
            original = readme.read_text(encoding="utf-8") + private_path + "\n"
            readme.write_text(original, encoding="utf-8")

            result = migrator.execute_prompt_upgrade(root, "0.5.1")

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "privacy_review_required")
            self.assertEqual(result["agent_action"], "report_privacy_findings")
            self.assertEqual(result["mutation_log"], [])
            self.assertFalse((root / "PLANS.md").exists())
            self.assertEqual(readme.read_text(encoding="utf-8"), original)

    def test_direct_apply_stops_without_writes_on_privacy_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            readme = root / "README.md"
            original = readme.read_text(encoding="utf-8") + "/" + "home" + "/sample/private\n"
            readme.write_text(original, encoding="utf-8")
            before = snapshot(root)

            result = migrator.apply_migration(root, "0.5.1")

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "privacy_review_required")
            self.assertFalse(result["validation_result"]["privacy"])
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

    def test_prompt_rechecks_privacy_immediately_before_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            original_report = migrator.build_migration_report
            calls = {"count": 0}

            def introduce_after_first_report(*args, **kwargs):
                report = original_report(*args, **kwargs)
                calls["count"] += 1
                if calls["count"] == 1:
                    (root / "late-note.md").write_text(
                        "/" + "Users" + "/sample/introduced-after-review\n",
                        encoding="utf-8",
                    )
                return report

            with mock.patch.object(migrator, "build_migration_report", side_effect=introduce_after_first_report):
                result = migrator.execute_prompt_upgrade(root, "0.5.1")

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "privacy_review_required")
            self.assertEqual(result["agent_action"], "report_privacy_findings")
            self.assertEqual(result["mutation_log"], [])
            self.assertFalse((root / "PLANS.md").exists())

    def test_parent_directory_swap_to_symlink_cannot_redirect_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "repo"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            make_target(root)
            original_write = migrator._SecureRoot.write_text
            swapped = {"done": False}

            def swap_before_docs_write(secure_root, relative, text):
                if relative == common.CANONICAL_FILES["principles"] and not swapped["done"]:
                    swapped["done"] = True
                    os.replace(root / "docs", root / "docs-original")
                    (root / "docs").symlink_to(outside, target_is_directory=True)
                return original_write(secure_root, relative, text)

            with mock.patch.object(migrator._SecureRoot, "write_text", new=swap_before_docs_write):
                result = migrator.apply_migration(root, "0.5.1")

            self.assertFalse(result["success"])
            self.assertIn(result["update_status"], {"rolled_back", "rollback_failed"})
            self.assertEqual(list(outside.iterdir()), [])

    def test_root_inode_swap_after_report_is_refused_without_outside_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "repo"
            moved = base / "repo-original"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            make_target(root)
            original_report = migrator.build_migration_report

            def replace_root_after_report(*args, **kwargs):
                report = original_report(*args, **kwargs)
                os.replace(root, moved)
                root.symlink_to(outside, target_is_directory=True)
                return report

            with mock.patch.object(migrator, "build_migration_report", side_effect=replace_root_after_report):
                result = migrator.apply_migration(root, "0.5.1")

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "root_identity_changed")
            self.assertEqual(list(outside.iterdir()), [])
            root.unlink()
            shutil.move(moved, root)

    def test_missing_and_existing_manifest_versions_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            missing = migrator.build_migration_report(root, "0.5.0")
            self.assertEqual(missing["current_workflow_version"], "unknown")
            manifest = root / "docs" / "codex" / "ENGINEERING_WORKFLOW_STATE.yaml"
            manifest.write_text("schema_version: 1\nskill_version: \"0.4.1\"\nmanaged_paths: []\n", encoding="utf-8")
            existing = migrator.build_migration_report(root, "0.5.0")
            self.assertEqual(existing["current_workflow_version"], "0.4.1")
            self.assertIn("docs/codex/ENGINEERING_WORKFLOW_STATE.yaml", existing["managed_paths"])

    def test_protected_unknown_and_shared_files_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            agents = root / "AGENTS.md"
            agents.write_text("# Existing owner\n", encoding="utf-8")
            protected_paths = (
                root / "docs" / "architecture" / "system.md",
                root / "docs" / "codex" / "team-notes.md",
                root / "docs" / "engineering" / "service-notes.md",
                agents,
            )
            before = {path: path.read_bytes() for path in protected_paths}
            result = migrator.apply_migration(root, "0.5.0")
            self.assertTrue(result["success"], result)
            self.assertEqual({path: path.read_bytes() for path in protected_paths}, before)
            report = migrator.build_migration_report(root, "0.5.0")
            self.assertIn("docs/codex/team-notes.md", report["ownership"]["unknown"])
            self.assertIn("docs/engineering/service-notes.md", report["ownership"]["unknown"])

    def test_unrelated_active_plan_requires_targeted_question_and_no_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            plans = root / "PLANS.md"
            original = "# Plans\n\n## Active Plan: Product Release\n\nStatus: in_progress\n"
            plans.write_text(original, encoding="utf-8")
            result = migrator.apply_migration(root, "0.5.0")
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "question_required")
            self.assertTrue(result["required_user_questions"])
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual(plans.read_text(encoding="utf-8"), original)

    def test_completed_plan_before_unrelated_active_plan_is_parsed_by_section(self):
        text = """# Plans

## Active Plan: Completed Maintenance

Status: done

## Active Plan: Product Release

Status: in_progress
"""
        conflict = migrator._existing_active_conflict(text)
        self.assertIsNotNone(conflict)
        self.assertIn("Product Release", conflict)

    def test_contradictory_rule_in_canonical_file_requires_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            agents = root / "AGENTS.md"
            agents.write_text("Use a lightweight plan for quick work.\n", encoding="utf-8")
            result = migrator.apply_migration(root, "0.5.0")
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "question_required")
            self.assertFalse((root / "PLANS.md").exists())
            self.assertEqual(agents.read_text(encoding="utf-8"), "Use a lightweight plan for quick work.\n")

    def test_symlinked_canonical_parent_requires_decision_and_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "repo"
            outside = base / "outside-docs"
            root.mkdir()
            outside.mkdir()
            (root / "README.md").write_text("# Target\n", encoding="utf-8")
            (root / "docs").symlink_to(outside, target_is_directory=True)
            result = migrator.apply_migration(root, "0.5.0")
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "question_required")
            self.assertFalse((root / "PLANS.md").exists())
            self.assertEqual(list(outside.iterdir()), [])

    def test_conflict_detection_covers_compressed_and_stale_completed_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            (root / "docs" / "notes.md").write_text("Use a lightweight plan for quick work.\n", encoding="utf-8")
            (root / "PLANS.md").write_text(
                "# Plans\n\n## Recently Completed\n\n- Finished. Resume from WQ-07.\n",
                encoding="utf-8",
            )
            report = migrator.build_migration_report(root, "0.5.0")
            kinds = {item["type"] for item in report["conflicts"]}
            self.assertIn("compressed_plan_rule", kinds)
            self.assertIn("stale_completed_state", kinds)

    def test_agent_config_is_untouched_without_explicit_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            config = root / ".codex" / "config.toml"
            config.parent.mkdir(parents=True)
            original = "custom = \"keep\"\n\n[agents]\nmax_threads = 4\nmax_depth = 2\n"
            config.write_text(original, encoding="utf-8")
            result = migrator.apply_migration(root, "0.5.0", include_agent_config=False)
            self.assertTrue(result["success"], result)
            self.assertEqual(config.read_text(encoding="utf-8"), original)
            self.assertFalse((root / ".codex" / "agents").exists())

    def test_structural_toml_merge_preserves_unknown_keys_and_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            config = root / ".codex" / "config.toml"
            config.parent.mkdir(parents=True)
            original = "custom = \"keep\"\n\n[agents]\nmax_threads = 4\n\n[profiles.custom]\nmode = \"custom\"\n"
            config.write_text(original, encoding="utf-8")
            result = migrator.apply_migration(root, "0.5.0", include_agent_config=True)
            self.assertTrue(result["success"], result)
            parsed = tomllib.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(parsed["custom"], "keep")
            self.assertEqual(parsed["agents"]["max_threads"], 4)
            self.assertEqual(parsed["agents"]["max_depth"], 1)
            self.assertEqual(parsed["profiles"]["custom"]["mode"], "custom")
            self.assertIn("+max_depth = 1", result["config_diff"])
            for name in ("utility", "explorer", "reviewer"):
                self.assertTrue((root / ".codex" / "agents" / f"{name}.toml").exists())

    def test_agents_header_comment_is_preserved_during_merge(self):
        text = "[agents] # keep this comment\nmax_threads = 3\n"
        merged, diff = migrator._merge_codex_config(text)
        self.assertIn("[agents] # keep this comment", merged)
        self.assertEqual(tomllib.loads(merged)["agents"]["max_depth"], 1)
        self.assertIn("+max_depth = 1", diff)

    def test_inline_agents_table_requires_explicit_migration_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            config = root / ".codex" / "config.toml"
            config.parent.mkdir(parents=True)
            original = "agents = { max_threads = 3 }\n"
            config.write_text(original, encoding="utf-8")
            result = migrator.apply_migration(root, "0.5.0", include_agent_config=True)
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "question_required")
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_conflicting_max_depth_is_preserved_and_requires_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            config = root / ".codex" / "config.toml"
            config.parent.mkdir(parents=True)
            original = "[agents]\nmax_depth = 2\n"
            config.write_text(original, encoding="utf-8")
            result = migrator.apply_migration(root, "0.5.0", include_agent_config=True)
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "question_required")
            self.assertEqual(config.read_text(encoding="utf-8"), original)
            self.assertFalse((root / "PLANS.md").exists())

    def test_manifest_contains_relative_exact_ownership_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            result = migrator.apply_migration(root, "0.5.0")
            self.assertTrue(result["success"], result)
            text = (root / "docs" / "codex" / "ENGINEERING_WORKFLOW_STATE.yaml").read_text(encoding="utf-8")
            private_prefix = "/" + "Users" + "/"
            self.assertNotIn(private_prefix, text)
            self.assertNotIn(str(root), text)
            self.assertIn("managed_paths:\n  - docs/codex/ENGINEERING_WORKFLOW_STATE.yaml", text)
            managed_lines = []
            in_managed = False
            for line in text.splitlines():
                if line == "managed_paths:":
                    in_managed = True
                    continue
                if in_managed and line.startswith("  - "):
                    managed_lines.append(line.removeprefix("  - "))
                    continue
                if in_managed:
                    break
            self.assertEqual(managed_lines, ["docs/codex/ENGINEERING_WORKFLOW_STATE.yaml"])
            self.assertIn('"docs/codex/team-notes.md"', text)

    def test_existing_manifest_managed_path_is_classified_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            managed = root / "docs" / "codex" / "owned.md"
            managed.write_text("owned\n", encoding="utf-8")
            manifest = root / "docs" / "codex" / "ENGINEERING_WORKFLOW_STATE.yaml"
            manifest.write_text(
                "schema_version: 1\nskill_version: \"0.4.1\"\nmanaged_paths:\n  - docs/codex/owned.md\n",
                encoding="utf-8",
            )
            report = migrator.build_migration_report(root, "0.5.0")
            self.assertIn("docs/codex/owned.md", report["managed_paths"])
            self.assertIn("docs/codex/team-notes.md", report["ownership"]["unknown"])

    def test_vendor_tree_is_excluded_from_privacy_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            vendor_note = root / "node_modules" / "package" / "notes.md"
            vendor_note.parent.mkdir(parents=True)
            private_path = "/" + "home" + "/sample/vendor"
            vendor_note.write_text(private_path, encoding="utf-8")
            report = migrator.build_migration_report(root, "0.5.0")
            self.assertFalse(any(item["path"].startswith("node_modules/") for item in report["privacy_findings"]))


if __name__ == "__main__":
    unittest.main()
