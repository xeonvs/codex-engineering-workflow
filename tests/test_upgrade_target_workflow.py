from __future__ import annotations

import json
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
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def synthetic_review_lines() -> list[str]:
    return [
        "pass" + "word" + "=" + "synthetic-placeholder",
        "SERVICE_" + "TOKEN" + "=" + "synthetic-placeholder",
        "person" + "@" + "example.test",
        "service" + ".internal.test",
        "Bearer" + " " + "synthetic-placeholder",
    ]


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
            self.assertNotIn("## Active Plan:", plan_text)
            self.assertIn("## Recently Completed", plan_text)
            self.assertIn(
                "schema_version: 2", (root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").read_text(encoding="utf-8")
            )
            self.assertIn(
                "instruction_contract_version: 3",
                (root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "planning_contract_version: 2",
                (root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").read_text(encoding="utf-8"),
            )
            state_text = (root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").read_text(encoding="utf-8")
            self.assertIn('plan_archive_path: "docs/archive/plans"', state_text)
            self.assertIn('  - "docs/archive/plans/README.md"', state_text)
            self.assertIn("active_plan: null", state_text)
            self.assertTrue(result["validation_result"]["instruction_contract"])
            for relative in ("docs/README.md", "docs/codex/README.md", "docs/engineering/README.md"):
                self.assertTrue((root / relative).is_file(), relative)

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
            manifest_text = manifest.read_text(encoding="utf-8")
            self.assertIn('skill_version: "0.5.1"', manifest_text)
            self.assertIn("orchestration_contract_version: 3", manifest_text)

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

    def test_synthetic_findings_require_value_free_explicit_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            values = synthetic_review_lines()
            (root / "fixtures.md").write_text("\n".join(values) + "\n", encoding="utf-8")
            before = snapshot(root)

            result = migrator.execute_prompt_upgrade(root, "0.8.2")

            self.assertFalse(result["success"])
            self.assertEqual(result["agent_action"], "request_privacy_review_approval")
            self.assertEqual(result["privacy_review"]["status"], "approval_required")
            self.assertRegex(result["privacy_review"]["review_token"], r"^privacy-review-v1:[0-9a-f]{64}$")
            self.assertEqual(
                {item["type"] for item in result["privacy_review"]["candidates"]},
                set(common.PRIVACY_REVIEW_ELIGIBLE_TYPES),
            )
            self.assertTrue(
                all(set(item) == {"type", "path", "line"} for item in result["privacy_review"]["candidates"])
            )
            serialized = json.dumps(result, sort_keys=True)
            for value in values:
                self.assertNotIn(value, serialized)
            self.assertNotIn("line_sha256", serialized)
            self.assertEqual(snapshot(root), before)
            self.assertFalse((root / "PLANS.md").exists())

    def test_exact_review_token_allows_migration_and_preserves_fixture_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            fixture = root / "fixtures.md"
            fixture.write_text("\n".join(synthetic_review_lines()) + "\n", encoding="utf-8")
            expected = fixture.read_bytes()
            report = migrator.build_migration_report(root, "0.8.2")
            review_value = report["privacy_review"]["review_token"]

            result = migrator.apply_migration(root, "0.8.2", approved_privacy_review=review_value)

            self.assertTrue(result["success"], result)
            self.assertEqual(result["privacy_review"]["status"], "approved")
            self.assertEqual(
                result["privacy_review"]["approved_count"],
                len(report["privacy_review"]["candidates"]),
            )
            self.assertEqual(result["privacy_findings"], [])
            self.assertEqual(fixture.read_bytes(), expected)
            self.assertFalse(any("privacy-review" in path.name.lower() for path in root.rglob("*")))

    def test_new_changed_and_moved_findings_invalidate_review_token_without_writes(self):
        mutations = {
            "new": lambda path: path.write_text(
                path.read_text(encoding="utf-8") + "second" + "@" + "example.test\n",
                encoding="utf-8",
            ),
            "changed": lambda path: path.write_text(
                path.read_text(encoding="utf-8").replace("person" + "@", "other" + "@"),
                encoding="utf-8",
            ),
            "moved": lambda path: path.write_text(
                "header\n" + path.read_text(encoding="utf-8"),
                encoding="utf-8",
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_target(root)
                fixture = root / "fixtures.md"
                fixture.write_text("\n".join(synthetic_review_lines()) + "\n", encoding="utf-8")
                review_value = migrator.build_migration_report(root, "0.8.2")["privacy_review"]["review_token"]
                mutate(fixture)
                before = snapshot(root)

                result = migrator.apply_migration(root, "0.8.2", approved_privacy_review=review_value)

                self.assertFalse(result["success"])
                self.assertEqual(result["privacy_review"]["status"], "token_mismatch")
                self.assertEqual(result["mutation_log"], [])
                self.assertEqual(snapshot(root), before)

    def test_malformed_and_version_bound_tokens_never_authorize_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            fixture = root / "fixtures.md"
            fixture.write_text("\n".join(synthetic_review_lines()) + "\n", encoding="utf-8")
            report = migrator.build_migration_report(root, "0.8.2")
            review_value = report["privacy_review"]["review_token"]

            malformed = migrator.apply_migration(root, "0.8.2", approved_privacy_review="not-a-review-token")
            self.assertEqual(malformed["privacy_review"]["status"], "token_mismatch")
            self.assertEqual(malformed["mutation_log"], [])

            other_target = migrator.apply_migration(root, "0.8.3", approved_privacy_review=review_value)
            self.assertEqual(other_target["privacy_review"]["status"], "token_mismatch")
            self.assertEqual(other_target["mutation_log"], [])
            self.assertNotEqual(
                review_value,
                migrator.build_migration_report(root, "0.8.3")["privacy_review"]["review_token"],
            )

            manifest = root / "docs" / "codex" / "ENGINEERING_WORKFLOW_STATE.yaml"
            manifest.write_text(
                'schema_version: 2\nskill_version: "0.8.0"\nmanaged_paths: []\n',
                encoding="utf-8",
            )
            current_version_review = migrator.build_migration_report(root, "0.8.2")["privacy_review"]["review_token"]
            self.assertNotEqual(review_value, current_version_review)
            self.assertFalse((root / "PLANS.md").exists())

    def test_stale_token_is_ignored_when_review_is_not_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)

            result = migrator.apply_migration(
                root,
                "0.8.2",
                approved_privacy_review="privacy-review-v1:" + ("0" * 64),
            )

            self.assertTrue(result["success"], result)
            self.assertEqual(result["privacy_review"]["status"], "not_required")
            self.assertEqual(result["privacy_review"]["approved_count"], 0)

    def test_disappeared_review_candidate_needs_no_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            fixture = root / "fixtures.md"
            fixture.write_text("person" + "@" + "example.test\n", encoding="utf-8")
            review_value = migrator.build_migration_report(root, "0.8.2")["privacy_review"]["review_token"]
            fixture.unlink()

            result = migrator.apply_migration(root, "0.8.2", approved_privacy_review=review_value)

            self.assertTrue(result["success"], result)
            self.assertEqual(result["privacy_review"]["status"], "not_required")

    def test_hard_privacy_category_cannot_be_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            fixture = root / "fixtures.md"
            fixture.write_text("\n".join(synthetic_review_lines()) + "\n", encoding="utf-8")
            eligible_review = migrator.build_migration_report(root, "0.8.2")["privacy_review"]["review_token"]
            fixture.write_text(
                fixture.read_text(encoding="utf-8") + "/" + "Users" + "/sample/private\n",
                encoding="utf-8",
            )
            before = snapshot(root)

            result = migrator.execute_prompt_upgrade(
                root,
                "0.8.2",
                approved_privacy_review=eligible_review,
            )

            self.assertFalse(result["success"])
            self.assertEqual(result["privacy_review"]["status"], "hard_block")
            self.assertIsNone(result["privacy_review"]["review_token"])
            self.assertEqual(result["agent_action"], "report_privacy_findings")
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

    def test_finding_introduced_during_approved_apply_triggers_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            fixture = root / "fixtures.md"
            fixture.write_text("\n".join(synthetic_review_lines()) + "\n", encoding="utf-8")
            review_value = migrator.build_migration_report(root, "0.8.2")["privacy_review"]["review_token"]
            original_final_scan = migrator._new_privacy_findings

            def introduce_before_final_scan(scan_root, approved):
                (root / "late-note.md").write_text("late" + "@" + "example.test\n", encoding="utf-8")
                return original_final_scan(scan_root, approved)

            with mock.patch.object(migrator, "_new_privacy_findings", side_effect=introduce_before_final_scan):
                result = migrator.apply_migration(root, "0.8.2", approved_privacy_review=review_value)

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "privacy_review_required")
            self.assertEqual(result["privacy_review"]["status"], "approval_required")
            self.assertTrue((root / "PLANS.md").is_file())
            self.assertFalse((root / "AGENTS.md").exists())
            self.assertFalse((root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").exists())
            self.assertTrue((root / "late-note.md").is_file())

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
            manifest.write_text('schema_version: 1\nskill_version: "0.4.1"\nmanaged_paths: []\n', encoding="utf-8")
            existing = migrator.build_migration_report(root, "0.5.0")
            self.assertEqual(existing["current_workflow_version"], "0.4.1")
            self.assertIn("docs/codex/ENGINEERING_WORKFLOW_STATE.yaml", existing["managed_paths"])

    def test_customized_v1_instruction_routes_to_model_review_without_writes(self):
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
            result = migrator.execute_prompt_upgrade(root, "0.8.0")
            self.assertFalse(result["success"], result)
            self.assertEqual(result["update_status"], "instruction_migration_required")
            self.assertEqual(result["agent_action"], "review_instruction_migration")
            self.assertEqual(result["required_user_questions"], [])
            self.assertEqual(result["instruction_contract"]["required_contract_version"], 3)
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual({path: path.read_bytes() for path in protected_paths}, before)

    def test_pristine_rendered_v1_templates_auto_migrate_to_contract_v3(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            agents_v2 = (migrator.TEMPLATE_ROOT / "AGENTS.md.tmpl").read_text(encoding="utf-8")
            agents_v2 = agents_v2.replace(
                'triggers="PLANS.md|docs/codex/TASKS_BACKLOG.md|docs/archive/**|workflow-state plan archive|plan closure"',
                'triggers="PLANS.md|docs/codex/TASKS_BACKLOG.md|docs/archive/**"',
            ).replace(
                "plan, backlog, closure, or default/custom workflow-state archive",
                "plan, backlog, closure, or archive",
            )
            route_start = agents_v2.index('<!-- ew:route id="long-running-execution"')
            route_end = agents_v2.index("\n## Route Maintenance", route_start)
            agents_v1 = (agents_v2[:route_start].rstrip() + "\n\n" + agents_v2[route_end:].lstrip("\n")).replace(
                "instruction_contract_version: 3", "instruction_contract_version: 1"
            )
            agents_v1 = agents_v1.replace("{{ entrypoint_hint }}", "README.md").replace("{{ subsystem_hint }}", ".")

            principles_v2 = (migrator.TEMPLATE_ROOT / "project_principles.md.tmpl").read_text(encoding="utf-8")
            new_rules = principles_v2.index('<!-- ew:invariant id="workflow.efficient-execution" -->')
            owned_refs = principles_v2.index("## Owned References", new_rules)
            principles_v1 = principles_v2[:new_rules] + principles_v2[owned_refs:]
            principles_v1 = (
                principles_v1.replace(
                    "- Long-running execution and waiter integrity: installed `engineering-workflow` skill, `references/agent_orchestration.md`.\n",
                    "",
                )
                .replace(
                    "- Validation and execution safety: installed `engineering-workflow` skill, `references/validation_safety.md`.\n",
                    "",
                )
                .replace(
                    "- Privacy and pre-push secret gating: installed `engineering-workflow` skill, "
                    "`references/privacy_and_sanitization.md`.\n",
                    "",
                )
            )

            (root / "AGENTS.md").write_text(agents_v1, encoding="utf-8")
            principles = root / common.CANONICAL_FILES["principles"]
            principles.write_text(principles_v1, encoding="utf-8")
            self.assertTrue(migrator._is_pristine_legacy("AGENTS.md", agents_v1))
            self.assertTrue(migrator._is_pristine_legacy(common.CANONICAL_FILES["principles"], principles_v1))

            result = migrator.apply_migration(root, "0.8.0")

            self.assertTrue(result["success"], result)
            self.assertIn("instruction_contract_version: 3", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("workflow.completion-driven-wait", principles.read_text(encoding="utf-8"))
            self.assertIn("workflow.review-before-commit", principles.read_text(encoding="utf-8"))
            manifest = (root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").read_text(encoding="utf-8")
            self.assertIn('skill_version: "0.8.0"', manifest)
            self.assertIn("orchestration_contract_version: 3", manifest)

    def test_customized_v2_requires_model_review_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            agents = (migrator.TEMPLATE_ROOT / "AGENTS.md.tmpl").read_text(encoding="utf-8")
            agents = agents.replace("instruction_contract_version: 3", "instruction_contract_version: 2")
            agents = agents.replace("{{ entrypoint_hint }}", "custom-entry.md").replace("{{ subsystem_hint }}", "app/")
            agents += "\nRepository-specific review route note.\n"
            (root / "AGENTS.md").write_text(agents, encoding="utf-8")
            principles_v3 = (migrator.TEMPLATE_ROOT / "project_principles.md.tmpl").read_text(encoding="utf-8")
            review_start = principles_v3.index('<!-- ew:invariant id="workflow.review-before-commit" -->')
            wait_start = principles_v3.index('<!-- ew:invariant id="workflow.completion-driven-wait" -->', review_start)
            principles_v2 = principles_v3[:review_start] + principles_v3[wait_start:]
            principles_v2 = principles_v2.replace(
                "\nBefore every authorized push, follow the installed `engineering-workflow` privacy reference: scan "
                "the final public tree and every ref the push can expose, keep candidate values out of agent output, "
                "and block the push until every finding is safely classified and remediated. Never weaken a scanner "
                "or rewrite history merely to make the gate green.\n",
                "",
            ).replace(
                "- Privacy and pre-push secret gating: installed `engineering-workflow` skill, "
                "`references/privacy_and_sanitization.md`.\n",
                "",
            )
            principles = root / common.CANONICAL_FILES["principles"]
            principles.write_text(principles_v2 + "\nRepository-specific ownership note.\n", encoding="utf-8")
            before = {
                root / "AGENTS.md": (root / "AGENTS.md").read_bytes(),
                principles: principles.read_bytes(),
            }

            result = migrator.execute_prompt_upgrade(root, "0.9.0")

            self.assertFalse(result["success"], result)
            self.assertEqual(result["update_status"], "instruction_migration_required")
            self.assertEqual(result["agent_action"], "review_instruction_migration")
            self.assertEqual(result["required_user_questions"], [])
            self.assertEqual(result["instruction_contract"]["required_contract_version"], 3)
            self.assertEqual(
                result["instruction_contract"]["missing_required_invariants"],
                ["workflow.review-before-commit"],
            )
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_pristine_rendered_v2_templates_auto_migrate_to_contract_v3(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            agents_v3 = (migrator.TEMPLATE_ROOT / "AGENTS.md.tmpl").read_text(encoding="utf-8")
            agents_v2 = agents_v3.replace("instruction_contract_version: 3", "instruction_contract_version: 2")
            agents_v2 = agents_v2.replace(
                'triggers="PLANS.md|docs/codex/TASKS_BACKLOG.md|docs/archive/**|workflow-state plan archive|plan closure"',
                'triggers="PLANS.md|docs/codex/TASKS_BACKLOG.md|docs/archive/**"',
            ).replace(
                "plan, backlog, closure, or default/custom workflow-state archive",
                "plan, backlog, closure, or archive",
            )
            agents_v2 = agents_v2.replace("{{ entrypoint_hint }}", "README.md").replace("{{ subsystem_hint }}", ".")

            principles_v3 = (migrator.TEMPLATE_ROOT / "project_principles.md.tmpl").read_text(encoding="utf-8")
            review_start = principles_v3.index('<!-- ew:invariant id="workflow.review-before-commit" -->')
            wait_start = principles_v3.index('<!-- ew:invariant id="workflow.completion-driven-wait" -->', review_start)
            principles_v2 = principles_v3[:review_start] + principles_v3[wait_start:]
            principles_v2 = principles_v2.replace(
                "\nBefore every authorized push, follow the installed `engineering-workflow` privacy reference: scan "
                "the final public tree and every ref the push can expose, keep candidate values out of agent output, "
                "and block the push until every finding is safely classified and remediated. Never weaken a scanner "
                "or rewrite history merely to make the gate green.\n",
                "",
            ).replace(
                "- Privacy and pre-push secret gating: installed `engineering-workflow` skill, "
                "`references/privacy_and_sanitization.md`.\n",
                "",
            )

            (root / "AGENTS.md").write_text(agents_v2, encoding="utf-8")
            principles = root / common.CANONICAL_FILES["principles"]
            principles.write_text(principles_v2, encoding="utf-8")
            self.assertTrue(migrator._is_pristine_legacy("AGENTS.md", agents_v2))
            self.assertTrue(migrator._is_pristine_legacy(common.CANONICAL_FILES["principles"], principles_v2))

            result = migrator.apply_migration(root, "0.9.0")

            self.assertTrue(result["success"], result)
            self.assertIn("instruction_contract_version: 3", (root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("workflow.review-before-commit", principles.read_text(encoding="utf-8"))
            manifest = (root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").read_text(encoding="utf-8")
            self.assertIn('skill_version: "0.9.0"', manifest)
            self.assertIn("instruction_contract_version: 3", manifest)

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

    def test_v2_active_plan_requires_a_migration_decision(self):
        text = """# Plans

## Active Plan: Product Release

Status: active
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

    def test_compact_checked_queue_rule_requires_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            agents = root / "AGENTS.md"
            original = "Use a compact checked queue item for bounded changes.\n"
            agents.write_text(original, encoding="utf-8")
            result = migrator.apply_migration(root, "0.6.0")
            self.assertEqual(result["update_status"], "question_required")
            self.assertFalse((root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").exists())
            self.assertEqual(agents.read_text(encoding="utf-8"), original)

    def test_known_pristine_legacy_pitfalls_is_auto_migrated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            pitfalls = root / common.CANONICAL_FILES["pitfalls"]
            pitfalls.write_text(
                "# Agent Execution Pitfalls\n\n"
                "Record recurring failure classes discovered during real work. Each entry names the trigger, broader failure, better default, and promotion or cleanup condition.\n\n"
                "## Entries\n\n"
                "### <short failure-class title>\n\n"
                "- Trigger: <repeatable situation>.\n"
                "- Failure class: <general mistake, not a one-off complaint>.\n"
                "- Better default: <specific preventive behavior>.\n"
                "- Evidence: <issue, plan, test, or incident reference>.\n"
                "- Lifecycle: <keep here, promote to project principles, or remove after the guardrail exists>.\n\n"
                "Do not duplicate the full planning contract here. Link actionable inactive follow-up work from `docs/codex/TASKS_BACKLOG.md` and promote it into `PLANS.md` only when work begins.\n",
                encoding="utf-8",
            )
            self.assertTrue(
                migrator._is_pristine_legacy(common.CANONICAL_FILES["pitfalls"], pitfalls.read_text(encoding="utf-8"))
            )
            result = migrator.apply_migration(root, "0.6.0")
            self.assertTrue(result["success"], result)
            self.assertIn("incident_schema_version: 1", pitfalls.read_text(encoding="utf-8"))

    def test_instruction_failure_rolls_back_before_version_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            failure = {
                "success": False,
                "status": "guard_missing",
                "routes": [],
                "invariants": [],
                "incidents": [],
                "errors": [{"code": "guard_missing", "path": "AGENTS.md", "detail": "synthetic"}],
                "warnings": [],
            }
            with mock.patch.object(migrator, "check_instruction_contract", return_value=failure):
                result = migrator.apply_migration(root, "0.6.0")
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "rolled_back")
            self.assertFalse((root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").exists())
            self.assertFalse((root / "AGENTS.md").exists())

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
            original = 'custom = "keep"\n\n[agents]\nmax_threads = 4\nmax_depth = 2\n'
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
            original = 'custom = "keep"\n\n[agents]\nmax_threads = 4\n\n[profiles.custom]\nmode = "custom"\n'
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
            self.assertEqual(
                managed_lines,
                [
                    "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml",
                    '"docs/archive/plans/README.md"',
                    '"docs/archive/README.md"',
                    '"docs/README.md"',
                ],
            )
            self.assertIn('"docs/codex/team-notes.md"', text)

    def test_manifest_preserves_complete_custom_archive_contract(self):
        existing = (
            "schema_version: 2\n"
            "managed_paths:\n"
            "  - docs/codex/ENGINEERING_WORKFLOW_STATE.yaml\n"
            "  - docs/product/PLANS_ARCHIVE.md\n"
            "  - docs/README.md\n"
            "plan_archive_path: docs/product/plans/archive\n"
            "plan_archive_indexes:\n"
            "  - docs/product/PLANS_ARCHIVE.md\n"
            "  - docs/README.md\n"
            "active_plan: null\n"
        )

        rendered = migrator._manifest_text("0.8.3", [], ["PLANS.md"], False, existing)

        self.assertIn('plan_archive_path: "docs/product/plans/archive"', rendered)
        self.assertIn('  - "docs/product/PLANS_ARCHIVE.md"', rendered)
        self.assertIn('  - "docs/README.md"', rendered)
        self.assertIn('active_plan: "PLANS.md"', rendered)
        self.assertNotIn('plan_archive_path: "docs/archive/plans"', rendered)

    def test_manifest_rejects_partial_custom_archive_contract(self):
        existing = "plan_archive_path: docs/product/plans/archive\nactive_plan: null\n"

        with self.assertRaises(migrator.MigrationConflict) as error:
            migrator._manifest_text("0.8.3", [], ["PLANS.md"], False, existing)

        self.assertEqual(error.exception.code, "ambiguous_archive_ownership")

    def test_report_rejects_partial_archive_contract_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            state = root / common.STATE_MANIFEST_PATH
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(
                "schema_version: 2\n"
                'skill_version: "0.8.2"\n'
                "managed_paths: []\n"
                "plan_archive_path: docs/product/plans/archive\n"
                "active_plan: null\n",
                encoding="utf-8",
            )
            before = {
                path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()
            }

            result = migrator.build_migration_report(root, "0.9.0")

            self.assertFalse(result["success"], result)
            self.assertTrue(
                any(item["type"] == "ambiguous_archive_ownership" for item in result["conflicts"]),
                result,
            )
            self.assertEqual(len(result["required_user_questions"]), 1)
            self.assertEqual(
                {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()},
                before,
            )

    def test_existing_manifest_managed_path_is_classified_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            managed = root / "docs" / "codex" / "owned.md"
            managed.write_text("owned\n", encoding="utf-8")
            manifest = root / "docs" / "codex" / "ENGINEERING_WORKFLOW_STATE.yaml"
            manifest.write_text(
                'schema_version: 1\nskill_version: "0.4.1"\nmanaged_paths:\n  - docs/codex/owned.md\n',
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
