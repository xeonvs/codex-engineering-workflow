from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "skill/engineering-workflow/assets/templates/PLANS.md.tmpl"
lifecycle = load_script_module("plan_lifecycle")


def ready_plan() -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    text = text.replace("<short task title>", "Lifecycle Demo")
    text = text.replace("Status: active", "Status: ready_for_closure")
    text = text.replace("Last Updated: YYYY-MM-DD", "Last Updated: 2026-08-13")
    text = text.replace(
        "| REQ-001 | <complete outcome> | user prompt | WQ-01 | <observable acceptance criterion> | pending |",
        "| REQ-001 | Complete lifecycle demo | user prompt | WQ-01 | Lifecycle check passes | done |",
    )
    text = text.replace("- [ ] WQ-01 — Implement and validate REQ-001. `pending`", "- [x] WQ-01 — Implement and validate REQ-001. `done`")
    text = text.replace("- Not run yet.", "- 2026-08-13: lifecycle validation passed.")
    text = text.replace("- Start with WQ-01, the first unfinished queue item.", "- No unfinished in-scope work remains.")
    text = text.replace("- [ ]", "- [x]")
    text = text.replace(
        "- <commit, push, CI, or release work that is completed, explicitly out of scope, or handled after closure without appearing as unfinished implementation work>",
        "- Commit, push, CI, and release are outside this local task.",
    )
    text = text.replace("- <remaining risk, external follow-up, or `none`>", "- None.")
    return text


class PlanLifecycleTests(unittest.TestCase):
    def test_pending_requirement_blocks_closure(self):
        issues = lifecycle.closure_issues(ready_plan().replace("| done |", "| pending |", 1), require_ready=True)
        self.assertTrue(any("non-terminal" in item for item in issues))

    def test_stale_resume_point_blocks_done_archive(self):
        text = ready_plan().replace("Status: ready_for_closure", "Status: done")
        text = text.replace("No unfinished in-scope work remains.", "Continue with WQ-02.")
        issues = lifecycle.closure_issues(text, require_ready=True, archived=True)
        self.assertTrue(any("Resume Point" in item for item in issues))

    def test_pseudo_terminal_status_is_rejected(self):
        issues = lifecycle.closure_issues(
            ready_plan().replace("| done |", "| resolved_for_release_handoff |", 1),
            require_ready=True,
        )
        self.assertTrue(any("pseudo-terminal" in item or "invalid" in item for item in issues))

    def test_validation_must_not_predate_last_update(self):
        text = ready_plan().replace("Last Updated: 2026-08-13", "Last Updated: 2026-08-14")
        issues = lifecycle.closure_issues(text, require_ready=True)
        self.assertTrue(any("predates" in item for item in issues))

    def test_unclassified_future_delivery_blocks_closure(self):
        text = ready_plan().replace(
            "Commit, push, CI, and release are outside this local task.",
            "Push the branch and wait for CI later.",
        )
        issues = lifecycle.closure_issues(text, require_ready=True)
        self.assertTrue(any("Post-Close Delivery" in item for item in issues))

    def test_future_handoff_blocks_closure(self):
        text = ready_plan().replace("- None.", "- Continue implementation in WQ-02.")
        issues = lifecycle.closure_issues(text, require_ready=True)
        self.assertTrue(any("Handoff Notes" in item for item in issues))

    def test_archive_closure_creates_all_required_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PLANS.md").write_text(ready_plan(), encoding="utf-8")
            (root / "docs/codex").mkdir(parents=True)
            (root / "docs/engineering").mkdir(parents=True)
            (root / "docs/codex/TASKS_BACKLOG.md").write_text("# Backlog\n", encoding="utf-8")
            (root / "docs/engineering/project_principles.md").write_text("# Principles\n", encoding="utf-8")

            result = lifecycle.close_plan(root, "archive")

            self.assertTrue(result["success"], result)
            self.assertTrue((root / result["archive_path"]).is_file())
            for relative in (
                "docs/README.md",
                "docs/archive/README.md",
                "docs/archive/plans/README.md",
            ):
                self.assertTrue((root / relative).is_file(), relative)
            self.assertFalse((root / "docs/codex/README.md").exists())
            self.assertFalse((root / "docs/engineering/README.md").exists())
            self.assertFalse((root / "docs/archive/backlog").exists())
            self.assertNotIn("## Active Plan:", (root / "PLANS.md").read_text(encoding="utf-8"))
            self.assertTrue(lifecycle.check_plan_lifecycle(root)["success"])

    def test_compact_is_default_without_creating_archive_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PLANS.md").write_text(ready_plan(), encoding="utf-8")
            result = lifecycle.close_plan(root, "compact")
            self.assertIsNone(result["archive_path"])
            self.assertFalse((root / "docs/archive").exists())

    def test_atomic_failure_restores_original_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plans = root / "PLANS.md"
            original = ready_plan().encode("utf-8")
            plans.write_bytes(original)
            real_replace = lifecycle._replace_file
            calls = {"count": 0}

            def fail_second(source, target):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("synthetic replacement failure")
                real_replace(source, target)

            with mock.patch.object(lifecycle, "_replace_file", side_effect=fail_second):
                with self.assertRaises(OSError):
                    lifecycle.close_plan(root, "archive")

            self.assertEqual(plans.read_bytes(), original)
            self.assertFalse((root / "docs/archive").exists())

    def test_existing_unmanaged_index_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PLANS.md").write_text(ready_plan(), encoding="utf-8")
            (root / "docs").mkdir()
            index = root / "docs/README.md"
            index.write_text("# Repository-owned index\n", encoding="utf-8")
            with self.assertRaises(lifecycle.LifecycleError) as error:
                lifecycle.close_plan(root, "archive")
            self.assertEqual(error.exception.code, "unmanaged_index_conflict")
            self.assertEqual(index.read_text(encoding="utf-8"), "# Repository-owned index\n")

    def test_symbolic_index_target_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (root / "PLANS.md").write_text(ready_plan(), encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs/README.md").symlink_to(outside)

            with self.assertRaises(lifecycle.LifecycleError) as error:
                lifecycle.close_plan(root, "archive")

            self.assertEqual(error.exception.code, "unsafe_target_path")
            self.assertEqual(outside.read_text(encoding="utf-8"), "# Outside\n")

    def test_legacy_v1_archive_is_indexed_without_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "docs/archive/plans/legacy.md"
            archive.parent.mkdir(parents=True)
            original = "# Legacy\n\nplan_schema_version: 1\n\nStatus: done\n"
            archive.write_text(original, encoding="utf-8")
            writes = lifecycle.planned_index_writes(root)
            lifecycle.apply_writes_atomically(root, writes)
            result = lifecycle.check_plan_lifecycle(root)
            self.assertTrue(result["success"], result)
            self.assertEqual(archive.read_text(encoding="utf-8"), original)

    def test_empty_compatibility_archive_is_optional_and_custom_archive_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "docs/archive/plans").mkdir(parents=True)
            custom_archive = root / "docs/product/plans/archive/retained.md"
            custom_archive.parent.mkdir(parents=True)
            custom_archive.write_text("# Repository-owned retained plan\n", encoding="utf-8")
            custom_index = root / "docs/product/PLANS_ARCHIVE.md"
            custom_index.write_text("# Repository-owned archive index\n", encoding="utf-8")
            (root / "docs/codex").mkdir(parents=True)
            (root / "PLANS.md").write_text(
                "# Execution Plans\n\nplan_schema_version: 2\n",
                encoding="utf-8",
            )
            (root / "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml").write_text(
                "schema_version: 2\n"
                "skill_name: engineering-workflow\n"
                "skill_version: \"0.8.1\"\n"
                "instruction_contract_version: 2\n"
                "protected_paths:\n"
                "  - docs/product/PLANS_ARCHIVE.md\n"
                "  - docs/product/plans/archive/retained.md\n",
                encoding="utf-8",
            )
            (root / "docs/codex/README.md").write_text(
                "# Workflow Documentation\n\n"
                f"{lifecycle.INDEX_START}\n"
                "No indexed documents yet.\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            (root / "docs/README.md").write_text(
                "# Documentation Index\n\n"
                f"{lifecycle.INDEX_START}\n"
                "- [codex/README.md](codex/README.md)\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            before_files = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            before_dirs = sorted(
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_dir()
            )

            result = lifecycle.check_plan_lifecycle(root)

            self.assertTrue(result["success"], result)
            self.assertNotIn("docs/archive/README.md", result["archive_indexes"]["required"])
            self.assertNotIn("docs/archive/plans/README.md", result["archive_indexes"]["required"])
            self.assertEqual(
                {
                    path.relative_to(root).as_posix(): path.read_bytes()
                    for path in root.rglob("*")
                    if path.is_file()
                },
                before_files,
            )
            self.assertEqual(
                sorted(
                    path.relative_to(root).as_posix()
                    for path in root.rglob("*")
                    if path.is_dir()
                ),
                before_dirs,
            )

    def test_non_empty_canonical_archive_still_requires_an_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            archive = root / "docs/archive/plans/retained.md"
            archive.parent.mkdir(parents=True)
            archive.write_text("# Retained plan\n", encoding="utf-8")

            result = lifecycle.check_archive_indexes(root)

            self.assertFalse(result["success"])
            self.assertIn("docs/archive/plans/README.md", result["required"])
            self.assertIn(
                {
                    "code": "index_missing",
                    "path": "docs/archive/plans/README.md",
                    "detail": "docs/archive/plans",
                },
                result["errors"],
            )

    def test_empty_archive_unmanaged_readme_is_not_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            readme = root / "docs/archive/plans/README.md"
            readme.parent.mkdir(parents=True)
            readme.write_text("# Repository-owned archive notes\n", encoding="utf-8")

            result = lifecycle.check_archive_indexes(root)

            self.assertFalse(result["success"])
            self.assertIn("docs/archive/plans/README.md", result["required"])
            self.assertIn(
                {
                    "code": "index_unmanaged",
                    "path": "docs/archive/plans/README.md",
                    "detail": "managed marker block missing",
                },
                result["errors"],
            )

    def test_empty_archive_symbolic_readmes_are_not_skipped(self):
        for broken in (False, True):
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                readme = root / "docs/archive/plans/README.md"
                readme.parent.mkdir(parents=True)
                target = root / "outside.md"
                if not broken:
                    target.write_text("# Outside\n", encoding="utf-8")
                readme.symlink_to(target)

                result = lifecycle.check_archive_indexes(root)

                self.assertFalse(result["success"])
                self.assertIn("docs/archive/plans/README.md", result["required"])
                self.assertTrue(
                    any(
                        item["path"] == "docs/archive/plans/README.md"
                        and item["code"] in {"index_missing", "index_unsafe"}
                        for item in result["errors"]
                    ),
                    result,
                )


if __name__ == "__main__":
    unittest.main()
