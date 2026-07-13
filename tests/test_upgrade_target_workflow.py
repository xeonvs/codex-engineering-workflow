from __future__ import annotations

import tempfile
import tomllib
import unittest
from pathlib import Path

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
