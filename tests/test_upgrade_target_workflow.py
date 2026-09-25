from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
import tomllib
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from test_support import load_script_module

common = load_script_module("common")
migrator = load_script_module("upgrade_target_workflow")
lifecycle = load_script_module("plan_lifecycle")
LEGACY_INSTRUCTIONS = Path(__file__).resolve().parent / "fixtures/legacy_instructions"


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


def make_custom_archive_target(root: Path, *, unmanaged_leaf: bool = False) -> None:
    make_target(root)
    archive = root / "docs/product/plans/archive"
    archive.mkdir(parents=True)
    (archive / "previous.md").write_text("# Previously retained plan\n", encoding="utf-8")
    indexes = (
        "docs/product/plans/archive/README.md",
        "docs/product/PLANS_ARCHIVE.md",
        "docs/README.md",
    )
    (root / indexes[0]).write_text(
        "# Product Plan Archive\n\nOwner note before index.\n\n"
        + (
            "Repository-owned index without managed markers.\n"
            if unmanaged_leaf
            else f"{lifecycle.INDEX_START}\n- [previous.md](previous.md)\n{lifecycle.INDEX_END}\n"
        )
        + "\nOwner note after index.\n",
        encoding="utf-8",
    )
    (root / indexes[1]).write_text(
        f"# Product Plans\n\n{lifecycle.INDEX_START}\n- [Archive](plans/archive/README.md)\n{lifecycle.INDEX_END}\n",
        encoding="utf-8",
    )
    (root / indexes[2]).write_text(
        "# Documentation\n\nOwner note before index.\n\n"
        f"{lifecycle.INDEX_START}\n"
        "- [Product plans](product/PLANS_ARCHIVE.md)\n"
        f"{lifecycle.INDEX_END}\n"
        "\nOwner note after index.\n",
        encoding="utf-8",
    )
    state = root / common.STATE_MANIFEST_PATH
    state.write_text(
        "schema_version: 2\n"
        'skill_version: "0.9.9"\n'
        "managed_paths:\n"
        f"  - {common.STATE_MANIFEST_PATH}\n"
        + "".join(f"  - {path}\n" for path in indexes)
        + "plan_archive_path: docs/product/plans/archive\n"
        "plan_archive_indexes:\n" + "".join(f"  - {path}\n" for path in indexes) + "active_plan: null\n",
        encoding="utf-8",
    )


def synthetic_review_lines() -> list[str]:
    return [
        "pass" + "word" + "=" + "synthetic-placeholder",
        "SERVICE_" + "TOKEN" + "=" + "synthetic-placeholder",
        "person" + "@" + "example.test",
        "service" + ".internal.test",
        "Bearer" + " " + "synthetic-placeholder",
    ]


def synthetic_full_review_lines() -> list[str]:
    return [
        *synthetic_review_lines(),
        "/" + "Users" + "/developer/project/result.png",
        "/" + "home" + "/service/app",
        "C:" + "\\Users\\developer\\project",
        "file:" + "//" + "/tmp/bundle.js",
        "~/.ssh/" + "id_ed25519",
        "BEGIN " + "OPENSSH PRIVATE KEY",
        "ghp" + "_" + "A" * 20,
        "git" + "@" + "example.test:repo",
        "https://" + "sample:fake" + "@" + "example.test/repo",
    ]


class UpgradeTargetWorkflowTests(unittest.TestCase):
    def test_review_token_supports_surrogate_decoded_paths(self):
        fingerprints = Counter({("file_url", "fixtures/odd-\udcff.txt", 1, "a" * 64): 1})
        review = migrator._privacy_review_token(fingerprints, "0.9.8", "0.9.9")
        self.assertRegex(review, r"^privacy-review-v2:[0-9a-f]{64}$")

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

    def test_current_valid_target_is_a_noop_but_missing_artifact_is_repaired(self):
        for mode, include_config in (("apply", False), ("prompt", False), ("apply", True), ("prompt", True)):
            with self.subTest(mode=mode, include_config=include_config), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_target(root)
                first = migrator.apply_migration(root, "0.9.6", include_agent_config=include_config)
                self.assertTrue(first["success"], first)
                before = snapshot(root)

                if mode == "apply":
                    current = migrator.apply_migration(root, "0.9.6", include_agent_config=include_config)
                else:
                    current = migrator.execute_prompt_upgrade(root, "0.9.6", include_agent_config=include_config)

                self.assertTrue(current["success"], current)
                self.assertEqual(current["update_status"], "already_current")
                self.assertEqual(current["mutation_log"], [])
                self.assertEqual(snapshot(root), before)

                if mode == "prompt" and not include_config:
                    backlog = root / common.CANONICAL_FILES["backlog"]
                    backlog.unlink()
                    repaired = migrator.execute_prompt_upgrade(root, "0.9.6")
                    self.assertTrue(repaired["success"], repaired)
                    self.assertEqual(repaired["update_status"], "updated")
                    self.assertTrue(backlog.is_file())

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
            self.assertEqual(result["agent_action"], "request_privacy_review_approval")
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
            self.assertRegex(result["privacy_review"]["review_token"], r"^privacy-review-v2:[0-9a-f]{64}$")
            self.assertEqual(
                {item["type"] for item in result["privacy_review"]["candidates"]},
                {
                    "credential_like_assignment",
                    "environment_secret_assignment",
                    "email",
                    "internal_hostname",
                    "bearer_token",
                },
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

    def test_mixed_privacy_categories_need_fresh_v2_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            fixture = root / "fixtures.md"
            values = synthetic_full_review_lines()
            fixture.write_text("\n".join(values) + "\n", encoding="utf-8")
            before = snapshot(root)

            result = migrator.execute_prompt_upgrade(root, "0.8.2")

            self.assertFalse(result["success"])
            self.assertEqual(result["privacy_review"]["status"], "approval_required")
            self.assertRegex(result["privacy_review"]["review_token"], r"^privacy-review-v2:[0-9a-f]{64}$")
            self.assertEqual(
                {item["type"] for item in result["privacy_review"]["candidates"]}, set(common.PRIVACY_PATTERNS)
            )
            self.assertEqual(result["agent_action"], "request_privacy_review_approval")
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual(snapshot(root), before)
            serialized = json.dumps(result, sort_keys=True)
            self.assertNotIn("line_sha256", serialized)
            for value in values:
                self.assertNotIn(value, serialized)

            old = migrator.apply_migration(root, "0.8.2", approved_privacy_review="privacy-review-v1:" + "0" * 64)
            self.assertEqual(old["privacy_review"]["status"], "token_mismatch")
            self.assertEqual(old["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

            approved = migrator.apply_migration(
                root, "0.8.2", approved_privacy_review=result["privacy_review"]["review_token"]
            )
            self.assertTrue(approved["success"], approved)
            self.assertEqual(approved["privacy_review"]["status"], "approved")
            self.assertEqual(fixture.read_text(encoding="utf-8"), "\n".join(values) + "\n")
            self.assertEqual({item["type"] for item in common.scan_public_tree(root)}, set(common.PRIVACY_PATTERNS))

    def test_scanner_regex_self_match_is_reviewable_and_snapshot_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            scanner = root / "tests" / "test_privacy_scanner.py"
            scanner.parent.mkdir()
            scanner.write_text('FILE_URL_RE = re.compile(r"file:' + "//" + '")\n', encoding="utf-8")
            report = migrator.build_migration_report(root, "0.8.2")
            self.assertEqual(report["privacy_review"]["status"], "approval_required")
            self.assertIn(
                {"type": "file_url", "path": "tests/test_privacy_scanner.py", "line": 1},
                report["privacy_review"]["candidates"],
            )
            scanner.write_text("# moved\n" + scanner.read_text(encoding="utf-8"), encoding="utf-8")
            before = snapshot(root)

            stale = migrator.apply_migration(
                root, "0.8.2", approved_privacy_review=report["privacy_review"]["review_token"]
            )
            self.assertEqual(stale["privacy_review"]["status"], "token_mismatch")
            self.assertEqual(stale["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

    def test_duplicate_formerly_hard_finding_invalidates_token_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            fixture = root / "fixtures.md"
            line = "file:" + "//" + "/tmp/sample.txt\n"
            fixture.write_text(line, encoding="utf-8")
            report = migrator.build_migration_report(root, "0.8.2")
            self.assertEqual(report["privacy_review"]["contract_version"], 2)
            fixture.write_text(line + line, encoding="utf-8")
            before = snapshot(root)

            stale = migrator.apply_migration(
                root, "0.8.2", approved_privacy_review=report["privacy_review"]["review_token"]
            )
            self.assertEqual(stale["privacy_review"]["status"], "token_mismatch")
            self.assertEqual(stale["mutation_log"], [])
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
                (root / "late-note.md").write_text("file:" + "//" + "/tmp/new.txt\n", encoding="utf-8")
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
            self.assertEqual(result["agent_action"], "request_privacy_review_approval")
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
            agents_v2 = (LEGACY_INSTRUCTIONS / "AGENTS_0_9_0.md.tmpl").read_text(encoding="utf-8")
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

            principles_v2 = (LEGACY_INSTRUCTIONS / "project_principles_0_9_0.md.tmpl").read_text(encoding="utf-8")
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
            agents_v3 = (LEGACY_INSTRUCTIONS / "AGENTS_0_9_0.md.tmpl").read_text(encoding="utf-8")
            agents_v2 = agents_v3.replace("instruction_contract_version: 3", "instruction_contract_version: 2")
            agents_v2 = agents_v2.replace(
                'triggers="PLANS.md|docs/codex/TASKS_BACKLOG.md|docs/archive/**|workflow-state plan archive|plan closure"',
                'triggers="PLANS.md|docs/codex/TASKS_BACKLOG.md|docs/archive/**"',
            ).replace(
                "plan, backlog, closure, or default/custom workflow-state archive",
                "plan, backlog, closure, or archive",
            )
            agents_v2 = agents_v2.replace("{{ entrypoint_hint }}", "README.md").replace("{{ subsystem_hint }}", ".")

            principles_v3 = (LEGACY_INSTRUCTIONS / "project_principles_0_9_0.md.tmpl").read_text(encoding="utf-8")
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

    def test_prompt_upgrade_preserves_claude_settings_and_existing_codex_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            originals = {
                "CLAUDE.md": b"# Native project instructions\nPreserve the project model configuration.\n",
                ".claude/settings.json": b'{"model":"provider-custom-model","effortLevel":"high"}\n',
                ".claude/agents/reviewer.md": b"---\nname: reviewer\ndescription: Native reviewer\nmodel: inherit\n---\nReview assigned files.\n",
                ".codex/agents/reviewer.toml": b'name = "custom-reviewer"\nmodel = "custom-supported-model"\nmodel_reasoning_effort = "medium"\n',
            }
            for relative, content in originals.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

            result = migrator.execute_prompt_upgrade(root, "0.9.6")

            self.assertTrue(result["success"], result)
            self.assertFalse(result["include_agent_config"])
            for relative, content in originals.items():
                self.assertEqual((root / relative).read_bytes(), content, relative)
            self.assertFalse((root / ".codex/config.toml").exists())
            self.assertFalse((root / ".codex/agents/utility.toml").exists())

    def test_opted_in_agent_configuration_preserves_existing_reviewer_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            reviewer = root / ".codex/agents/reviewer.toml"
            reviewer.parent.mkdir(parents=True)
            original = 'name = "local-reviewer"\nmodel = "custom-supported-model"\nmodel_reasoning_effort = "medium"\n'
            reviewer.write_text(original, encoding="utf-8")

            result = migrator.apply_migration(root, "0.9.6", include_agent_config=True)

            self.assertTrue(result["success"], result)
            self.assertEqual(reviewer.read_text(encoding="utf-8"), original)

    def test_prior_opt_in_refreshes_only_pristine_agent_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            initial = migrator.apply_migration(root, "0.9.7", include_agent_config=True)
            self.assertTrue(initial["success"], initial)
            agents = root / ".codex/agents"
            for name in ("utility", "explorer", "reviewer"):
                path = agents / f"{name}.toml"
                prior = path.read_text(encoding="utf-8")
                if name == "utility":
                    prior = prior.replace('model = "gpt-6-luna"', 'model = "gpt-5.6-terra"')
                elif name == "explorer":
                    prior = prior.replace('model = "gpt-6-sol"', 'model = "gpt-5.6-terra"')
                else:
                    prior = prior.replace('model = "gpt-6-sol"', 'model = "gpt-6-astra"')
                    prior = prior.replace('model_reasoning_effort = "medium"', 'model_reasoning_effort = "high"')
                    prior = prior.replace(
                        "Bounded evidence-first review for ordinary changes",
                        "Evidence-first review for correctness and high-risk changes",
                    )
                self.assertTrue(migrator._is_pristine_prior_agent(name, prior))
                path.write_text(prior, encoding="utf-8")

            explorer = agents / "explorer.toml"
            custom = explorer.read_text(encoding="utf-8").replace(
                'model = "gpt-5.6-terra"', 'model = "custom-supported-model"'
            )
            explorer.write_text(custom, encoding="utf-8")
            report = migrator.build_migration_report(root, "0.9.8")
            self.assertTrue(report["include_agent_config"])
            proposed = {
                change["path"]
                for change in report["proposed_changes"]
                if change["reason"] == "known pristine prior agent template fingerprint"
            }
            self.assertEqual(proposed, {".codex/agents/utility.toml", ".codex/agents/reviewer.toml"})

            result = migrator.execute_prompt_upgrade(root, "0.9.8")
            self.assertTrue(result["success"], result)
            self.assertTrue(result["include_agent_config"])
            self.assertEqual(explorer.read_text(encoding="utf-8"), custom)
            for name in ("utility", "reviewer"):
                expected = (migrator.AGENT_TEMPLATE_ROOT / f"{name}.toml.tmpl").read_text(encoding="utf-8")
                self.assertEqual((agents / f"{name}.toml").read_text(encoding="utf-8"), expected)

    def test_prior_agent_template_is_not_changed_without_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            utility = root / ".codex/agents/utility.toml"
            utility.parent.mkdir(parents=True)
            current = (migrator.AGENT_TEMPLATE_ROOT / "utility.toml.tmpl").read_text(encoding="utf-8")
            prior = current.replace('model = "gpt-6-luna"', 'model = "gpt-5.6-terra"')
            utility.write_text(prior, encoding="utf-8")
            result = migrator.execute_prompt_upgrade(root, "0.9.8")
            self.assertTrue(result["success"], result)
            self.assertFalse(result["include_agent_config"])
            self.assertEqual(utility.read_text(encoding="utf-8"), prior)

    def test_invalid_codex_config_blocks_only_requested_configuration_work(self):
        for include_config in (False, True):
            with self.subTest(include_config=include_config), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_target(root)
                config = root / ".codex/config.toml"
                config.parent.mkdir()
                original = b"[agents\n"
                config.write_bytes(original)
                before = snapshot(root)

                result = migrator.execute_prompt_upgrade(root, "0.9.6", include_agent_config=include_config)

                self.assertEqual(config.read_bytes(), original)
                if include_config:
                    self.assertFalse(result["success"])
                    self.assertEqual(snapshot(root), before)
                    self.assertIn("invalid_codex_config", {item["type"] for item in result["conflicts"]})
                else:
                    self.assertTrue(result["success"], result)
                    self.assertFalse((root / ".codex/agents").exists())

    def test_symbolic_codex_config_is_preserved_without_configuration_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            (root / "native-settings.toml").write_text('model = "native-model"\n', encoding="utf-8")
            config = root / ".codex/config.toml"
            config.parent.mkdir()
            config.symlink_to("../native-settings.toml")

            report = migrator.build_migration_report(root, "0.9.6", include_agent_config=True)
            self.assertTrue(report["required_user_questions"])
            result = migrator.execute_prompt_upgrade(root, "0.9.6")

            self.assertTrue(result["success"], result)
            self.assertTrue(config.is_symlink())
            self.assertEqual(os.readlink(config), "../native-settings.toml")
            self.assertFalse((root / ".codex/agents").exists())

    def test_pristine_090_templates_gain_execution_routes_but_customized_owners_are_preserved(self):
        for customized in (False, True):
            with self.subTest(customized=customized), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_target(root)
                agents = (LEGACY_INSTRUCTIONS / "AGENTS_0_9_0.md.tmpl").read_text(encoding="utf-8")
                agents = agents.replace("{{ entrypoint_hint }}", "README.md").replace("{{ subsystem_hint }}", ".")
                principles = (LEGACY_INSTRUCTIONS / "project_principles_0_9_0.md.tmpl").read_text(encoding="utf-8")
                if customized:
                    agents += "\nProject-owned routing annotation.\n"
                    principles += "\nProject-owned policy annotation.\n"
                (root / "AGENTS.md").write_text(agents, encoding="utf-8")
                owner = root / common.CANONICAL_FILES["principles"]
                owner.write_text(principles, encoding="utf-8")

                result = migrator.execute_prompt_upgrade(root, "0.9.6")

                self.assertTrue(result["success"], result)
                if customized:
                    self.assertEqual((root / "AGENTS.md").read_text(encoding="utf-8"), agents)
                    self.assertEqual(owner.read_text(encoding="utf-8"), principles)
                else:
                    graph = migrator.check_instruction_contract(root)
                    self.assertTrue(graph["success"], graph)
                    context = next(route for route in graph["routes"] if route["id"] == "execution-context")
                    self.assertEqual(
                        context["owners"],
                        ["skill://engineering-workflow/references/platform_compatibility.md"],
                    )
                    self.assertNotIn("**", context["triggers"])
                    routes = {route["id"]: route for route in graph["routes"]}
                    self.assertEqual(
                        routes["scope-decision"]["owners"],
                        ["skill://engineering-workflow/references/question_matrix.md"],
                    )
                    self.assertEqual(
                        routes["task-handoff"]["owners"],
                        [
                            "skill://engineering-workflow/references/agent_orchestration.md",
                            "skill://engineering-workflow/references/planning_and_backlog.md",
                        ],
                    )
                    self.assertEqual(graph["contract_version"], 3)

    def test_prior_pristine_routes_upgrade_and_customized_routes_remain_owned(self):
        # Reconstruct only the changed prior blocks; hashes pin the actual released bytes.
        # Custom-byte preservation tests backend ownership, not semantic adoption;
        # the prompt workflow reviews affected customized owners before apply.
        old_route = (
            '<!-- ew:route id="execution-context" triggers="**" '
            'owners="skill://engineering-workflow/references/platform_compatibility.md|'
            "skill://engineering-workflow/references/question_matrix.md|"
            'skill://engineering-workflow/references/agent_orchestration.md" '
            'guards="manual_review:verify native host behavior scope authorization task continuity and handoff" -->\n'
            "| `execution-context` | every task, including clarification, steering, delegation, and handoff | "
            "platform reference first, then question policy and host-compatible shared orchestration sections | "
            "scope and host-capability review |\n\n"
        )
        old_wait = (
            "For long-running commands, follow the installed `engineering-workflow` completion-driven waiter "
            "and bounded-output contract. Keep full logs and required terminal results in private task-owned "
            "ignored artifacts, verify them independently of a possibly truncated waiter cell, and do not "
            "wake the model for periodic empty polls when the environment can wait for completion.\n"
        )
        for readme, source, customized in (
            (True, True, False),
            (True, False, False),
            (False, True, False),
            (False, False, False),
            (True, False, True),
        ):
            with (
                self.subTest(readme=readme, source=source, customized=customized),
                tempfile.TemporaryDirectory() as tmp,
            ):
                root = Path(tmp)
                make_target(root)
                if not readme:
                    (root / "README.md").unlink()
                if source:
                    (root / "src").mkdir()
                replacements = {
                    "entrypoint_hint": "README.md" if readme else ".",
                    "subsystem_hint": "src/" if source else ".",
                }
                expected_agents = migrator._template("AGENTS.md.tmpl", replacements)
                start = expected_agents.index('<!-- ew:route id="execution-context"')
                end = expected_agents.index('<!-- ew:route id="planning"')
                agents = expected_agents[:start] + old_route + expected_agents[end:]
                current_principles = migrator._template("project_principles.md.tmpl", {})
                expected_principles = current_principles
                context_start = expected_principles.index(
                    "Preserve correctness, safety, explicit requirements, and required evidence"
                )
                context_end = expected_principles.index(
                    '\n\n<!-- ew:invariant id="workflow.evidence-driven-completion" -->',
                    context_start,
                )
                old_execution = (
                    "Preserve correctness, safety, explicit requirements, and required evidence before optimizing "
                    "calls or output. Use bounded reconnaissance and focused inspection, but fully ingest sources "
                    "needed for exact edits; prefer repository-native automation and avoid unrelated work. Maintain "
                    "affected durable state as facts change before dependent actions or handoff, reuse still-current "
                    "task context, and do not create a periodic model loop that rewrites or rechecks unchanged state."
                )
                expected_principles = (
                    expected_principles[:context_start] + old_execution + expected_principles[context_end:]
                )
                start = expected_principles.index("For long-running commands,")
                end = expected_principles.index("\n## Owned References", start)
                principles = expected_principles[:start] + old_wait + expected_principles[end:]
                owner_path = common.CANONICAL_FILES["principles"]
                self.assertTrue(migrator._is_pristine_legacy("AGENTS.md", agents))
                self.assertTrue(migrator._is_pristine_legacy(owner_path, principles))
                if customized:
                    agents += "\nProject-owned routing annotation.\n"
                    principles += "\nProject-owned policy annotation.\n"
                (root / "AGENTS.md").write_text(agents, encoding="utf-8")
                owner = root / owner_path
                owner.write_text(principles, encoding="utf-8")
                before = snapshot(root)
                report = migrator.build_migration_report(root, "0.9.6")
                self.assertTrue(report["success"], report)
                self.assertEqual(snapshot(root), before)
                updates = {item["path"] for item in report["proposed_changes"] if item["action"] == "update"}
                self.assertEqual("AGENTS.md" in updates, not customized)
                self.assertEqual(owner_path in updates, not customized)
                result = migrator.execute_prompt_upgrade(root, "0.9.6")
                self.assertTrue(result["success"], result)
                self.assertEqual((root / "AGENTS.md").read_text(), agents if customized else expected_agents)
                self.assertEqual(owner.read_text(), principles if customized else current_principles)
                after = snapshot(root)
                repeated = migrator.execute_prompt_upgrade(root, "0.9.6")
                self.assertEqual(repeated["update_status"], "already_current")
                self.assertEqual(snapshot(root), after)

    def test_pristine_095_context_templates_upgrade_but_customized_owners_remain_protected(self):
        new_route = (
            '<!-- ew:route id="task-handoff" triggers="delegation|context recovery|execution handoff|'
            'large transient evidence" owners="skill://engineering-workflow/references/agent_orchestration.md|'
            'skill://engineering-workflow/references/planning_and_backlog.md" '
            'guards="manual_review:verify self-contained scope accessible evidence durable state and root acceptance" -->\n'
            "| `task-handoff` | delegation, context recovery, execution handoff, or large transient evidence | "
            "installed orchestration and planning references | self-contained scope, durable state, accessible evidence, "
            "and root acceptance |\n"
        )
        old_route = (
            '<!-- ew:route id="task-handoff" triggers="delegation|context recovery|execution handoff" '
            'owners="skill://engineering-workflow/references/agent_orchestration.md" '
            'guards="manual_review:verify scoped ownership and completion evidence" -->\n'
            "| `task-handoff` | delegation, context recovery, or execution handoff | "
            "relevant shared orchestration sections | scope, ownership, and completion evidence |\n"
        )
        new_principles = (
            "Preserve correctness, safety, explicit requirements, and required evidence before optimizing calls or "
            "output. Use bounded reconnaissance and focused inspection, but fully ingest sources needed for exact "
            "edits; prefer repository-native automation and avoid unrelated work. The root owns intent, plan, "
            "integration, final verification, and a current working representation of the task. Keep tightly coupled "
            "work with the root; give independent workers a bounded self-contained packet and require a compact result "
            "with findings, checks, blockers, and accessible artifact paths.\n\n"
            "Treat raw command output, searches, temporary diagnostics, and large logs as transient evidence that may "
            "stay outside root context. Preserve user constraints, accepted decisions, invariants, important verified "
            "facts, implementation state, blockers, and ordered remaining work as durable knowledge in `PLANS.md` or "
            "the appropriate repository owner before dependent work. Recover after context loss from the current plan, "
            "repository state, and relevant durable artifacts rather than reconstructing the full execution transcript. "
            "Do not create periodic state-maintenance loops or artifacts for observations that have no continuing value."
        )
        old_principles = (
            "Preserve correctness, safety, explicit requirements, and required evidence before optimizing calls or "
            "output. Use bounded reconnaissance and focused inspection, but fully ingest sources needed for exact "
            "edits; prefer repository-native automation and avoid unrelated work. Maintain affected durable state as "
            "facts change before dependent actions or handoff, reuse still-current task context, and do not create a "
            "periodic model loop that rewrites or rechecks unchanged state."
        )
        for readme, source, customized in (
            (True, True, False),
            (True, False, False),
            (False, True, False),
            (False, False, False),
            (True, False, True),
        ):
            with (
                self.subTest(readme=readme, source=source, customized=customized),
                tempfile.TemporaryDirectory() as tmp,
            ):
                root = Path(tmp)
                make_target(root)
                if not readme:
                    (root / "README.md").unlink()
                if source:
                    (root / "src").mkdir()
                agents = migrator._template(
                    "AGENTS.md.tmpl",
                    {
                        "entrypoint_hint": "README.md" if readme else ".",
                        "subsystem_hint": "src/" if source else ".",
                    },
                ).replace(new_route, old_route)
                principles = migrator._template("project_principles.md.tmpl", {}).replace(
                    new_principles,
                    old_principles,
                )
                self.assertTrue(migrator._is_pristine_legacy("AGENTS.md", agents))
                self.assertTrue(migrator._is_pristine_legacy(common.CANONICAL_FILES["principles"], principles))
                if customized:
                    agents += "\nProject-owned routing annotation.\n"
                    principles += "\nProject-owned policy annotation.\n"
                (root / "AGENTS.md").write_text(agents, encoding="utf-8")
                owner = root / common.CANONICAL_FILES["principles"]
                owner.write_text(principles, encoding="utf-8")
                result = migrator.execute_prompt_upgrade(root, "0.9.6")
                self.assertTrue(result["success"], result)
                if customized:
                    self.assertEqual((root / "AGENTS.md").read_text(encoding="utf-8"), agents)
                    self.assertEqual(owner.read_text(encoding="utf-8"), principles)
                else:
                    self.assertIn("large transient evidence", (root / "AGENTS.md").read_text(encoding="utf-8"))
                    self.assertIn("durable knowledge", owner.read_text(encoding="utf-8"))

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
            reviewer = tomllib.loads((root / ".codex/agents/reviewer.toml").read_text(encoding="utf-8"))
            self.assertEqual(reviewer["model"], "gpt-" + "6-sol")
            self.assertEqual(reviewer["model_reasoning_effort"], "medium")

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

    def test_upgrade_preserves_three_level_custom_archive_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_custom_archive_target(root)

            result = migrator.apply_migration(root, "0.9.10")

            self.assertTrue(result["success"], result)
            self.assertFalse((root / "docs/archive").exists())
            leaf = (root / "docs/product/plans/archive/README.md").read_text(encoding="utf-8")
            middle = (root / "docs/product/PLANS_ARCHIVE.md").read_text(encoding="utf-8")
            docs = (root / "docs/README.md").read_text(encoding="utf-8")
            self.assertIn("Owner note before index.", leaf)
            self.assertIn("Owner note after index.", leaf)
            self.assertIn("Owner note before index.", docs)
            self.assertIn("Owner note after index.", docs)
            self.assertEqual(leaf.count("(previous.md)"), 1)
            self.assertEqual(middle.count("(plans/archive/README.md)"), 1)
            self.assertEqual(docs.count("(product/PLANS_ARCHIVE.md)"), 1)
            self.assertTrue(lifecycle.check_plan_lifecycle(root)["success"])

            before = snapshot(root)
            repeat = migrator.apply_migration(root, "0.9.10")
            self.assertEqual(repeat["update_status"], "already_current", repeat)
            self.assertEqual(snapshot(root), before)

    def test_unmanaged_custom_archive_index_rolls_back_partial_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_custom_archive_target(root, unmanaged_leaf=True)
            before = snapshot(root)

            result = migrator.apply_migration(root, "0.9.10")

            self.assertFalse(result["success"], result)
            self.assertEqual(result["update_status"], "rolled_back")
            self.assertEqual(result["errors"][0]["code"], "unmanaged_index_conflict")
            after = snapshot(root)
            self.assertEqual({path: data for path, data in after.items() if path != "PLANS.md"}, before)
            self.assertIn("Apply failed", (root / "PLANS.md").read_text(encoding="utf-8"))
            self.assertFalse((root / "docs/archive").exists())

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
