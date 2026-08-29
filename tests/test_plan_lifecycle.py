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
    text = text.replace(
        "- [ ] WQ-01 — Implement and validate REQ-001. `pending`",
        "- [x] WQ-01 — Implement and validate REQ-001. `done`",
    )
    text = text.replace("- Not run yet.", "- 2026-08-13: lifecycle validation passed.")
    text = text.replace(
        "- Start with WQ-01, the first unfinished queue item.", "- No unfinished in-scope work remains."
    )
    text = text.replace("- [ ]", "- [x]")
    text = text.replace(
        "- <commit, push, CI, or release work that is completed, explicitly out of scope, or handled after closure without appearing as unfinished implementation work>",
        "- Commit, push, CI, and release are outside this local task.",
    )
    text = text.replace("- <remaining risk, external follow-up, or `none`>", "- None.")
    return text


def explicit_state(
    archive_path: str,
    indexes: list[str],
    *,
    active_plan: str = "PLANS.md",
    managed_paths: list[str] | None = None,
) -> str:
    managed_paths = managed_paths or [lifecycle.STATE_MANIFEST_PATH, *indexes]
    lines = [
        "schema_version: 2",
        "skill_name: engineering-workflow",
        'skill_version: "0.9.0"',
        "managed_paths:",
        *[f"  - {path}" for path in managed_paths],
        f"plan_archive_path: {archive_path}",
        "plan_archive_indexes:",
        *[f"  - {path}" for path in indexes],
        f"active_plan: {active_plan}",
        "instruction_contract_version: 3",
        "planning_contract_version: 2",
        "orchestration_contract_version: 3",
    ]
    return "\n".join(lines) + "\n"


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
                'skill_version: "0.8.1"\n'
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
                path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()
            }
            before_dirs = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())

            result = lifecycle.check_plan_lifecycle(root)

            self.assertTrue(result["success"], result)
            self.assertNotIn("docs/archive/README.md", result["archive_indexes"]["required"])
            self.assertNotIn("docs/archive/plans/README.md", result["archive_indexes"]["required"])
            self.assertEqual(
                {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()},
                before_files,
            )
            self.assertEqual(
                sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir()),
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

    def test_explicit_custom_archive_closure_updates_graph_and_state_without_default_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "PLANS.md").write_text(ready_plan(), encoding="utf-8")
            archive = root / "docs/product/plans/archive"
            archive.mkdir(parents=True)
            retained = archive / "retained.md"
            retained.write_text("# Retained plan\n", encoding="utf-8")
            leaf = root / "docs/product/PLANS_ARCHIVE.md"
            leaf.write_text(
                "# Product Plan Archive\n\n"
                f"{lifecycle.INDEX_START}\n"
                "- [retained.md](plans/archive/retained.md)\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            docs_index = root / "docs/README.md"
            docs_index.write_text(
                "# Documentation\n\n"
                f"{lifecycle.INDEX_START}\n"
                "- [codex/README.md](codex/README.md)\n"
                "- [Product plans](./product/PLANS_ARCHIVE.md)\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            state = root / lifecycle.STATE_MANIFEST_PATH
            state.parent.mkdir(parents=True)
            (root / "docs/codex/README.md").write_text(
                "# Workflow Documentation\n\n"
                f"{lifecycle.INDEX_START}\n"
                "No indexed documents yet.\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            state.write_text(
                explicit_state(
                    "docs/product/plans/archive",
                    ["docs/product/PLANS_ARCHIVE.md", "docs/README.md"],
                ),
                encoding="utf-8",
            )

            result = lifecycle.close_plan(root, "archive")

            self.assertTrue(result["success"], result)
            self.assertTrue(result["archive_path"].startswith("docs/product/plans/archive/"))
            self.assertTrue((root / result["archive_path"]).is_file())
            self.assertFalse((root / "docs/archive").exists())
            self.assertNotIn("## Active Plan:", (root / "PLANS.md").read_text(encoding="utf-8"))
            self.assertIn("active_plan: null", state.read_text(encoding="utf-8"))
            leaf_text = leaf.read_text(encoding="utf-8")
            self.assertEqual(leaf_text.count("retained.md"), 2)
            self.assertEqual(leaf_text.count(Path(result["archive_path"]).name), 2)
            self.assertEqual(docs_index.read_text(encoding="utf-8").count("product/PLANS_ARCHIVE.md"), 1)
            checked = lifecycle.check_plan_lifecycle(root)
            self.assertTrue(checked["success"], checked)
            self.assertEqual(checked["archive_layout"]["archive_path"], "docs/product/plans/archive")
            self.assertIsNone(checked["archive_layout"]["active_plan"])

    def test_partial_or_inconsistent_explicit_archive_state_fails_closed(self):
        cases = {
            "missing_indexes": (
                "plan_archive_path: docs/product/plans/archive\nactive_plan: PLANS.md\n",
                "archive_ownership_ambiguous",
            ),
            "duplicate_indexes": (
                explicit_state(
                    "docs/product/plans/archive",
                    ["docs/product/PLANS_ARCHIVE.md", "docs/product/PLANS_ARCHIVE.md"],
                ),
                "archive_ownership_ambiguous",
            ),
            "active_mismatch": (
                explicit_state(
                    "docs/product/plans/archive",
                    ["docs/product/PLANS_ARCHIVE.md"],
                    active_plan="null",
                ),
                "archive_active_plan_mismatch",
            ),
            "unsafe_path": (
                explicit_state("../outside", ["docs/product/PLANS_ARCHIVE.md"]),
                "archive_state_invalid",
            ),
            "duplicate_key": (
                explicit_state("docs/product/plans/archive", ["docs/product/PLANS_ARCHIVE.md"])
                + "plan_archive_path: docs/other/archive\n",
                "archive_state_invalid",
            ),
        }
        for name, (state_text, expected_code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                plans = root / "PLANS.md"
                plans.write_text(ready_plan(), encoding="utf-8")
                state = root / lifecycle.STATE_MANIFEST_PATH
                state.parent.mkdir(parents=True)
                state.write_text(state_text, encoding="utf-8")
                before = plans.read_bytes()

                with self.assertRaises(lifecycle.LifecycleError) as error:
                    lifecycle.close_plan(root, "archive")

                self.assertEqual(error.exception.code, expected_code)
                self.assertEqual(plans.read_bytes(), before)
                self.assertFalse((root / "docs/archive").exists())
                self.assertFalse((root / "docs/product/plans/archive").exists())

    def test_missing_or_unmanaged_custom_index_is_not_assumed_owned(self):
        for existing in (False, True):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                plans = root / "PLANS.md"
                plans.write_text(ready_plan(), encoding="utf-8")
                leaf = root / "docs/product/PLANS_ARCHIVE.md"
                if existing:
                    leaf.parent.mkdir(parents=True)
                    leaf.write_text("# Repository-owned archive\n", encoding="utf-8")
                state = root / lifecycle.STATE_MANIFEST_PATH
                state.parent.mkdir(parents=True, exist_ok=True)
                state.write_text(
                    explicit_state(
                        "docs/product/plans/archive",
                        ["docs/product/PLANS_ARCHIVE.md"],
                        managed_paths=[lifecycle.STATE_MANIFEST_PATH],
                    ),
                    encoding="utf-8",
                )
                before = {
                    path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()
                }

                with self.assertRaises(lifecycle.LifecycleError) as error:
                    lifecycle.close_plan(root, "archive")

                expected = "unmanaged_index_conflict" if existing else "archive_index_ownership_missing"
                self.assertEqual(error.exception.code, expected)
                self.assertEqual(
                    {
                        path.relative_to(root).as_posix(): path.read_bytes()
                        for path in root.rglob("*")
                        if path.is_file()
                    },
                    before,
                )

    def test_existing_parent_in_empty_explicit_graph_is_still_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "PLANS.md").write_text(
                "# Execution Plans\n\nplan_schema_version: 2\n\n## Recently Completed\n",
                encoding="utf-8",
            )
            parent = root / "docs/product/PLANS_ARCHIVE.md"
            parent.parent.mkdir(parents=True)
            parent.write_text("# Repository-owned archive index without markers\n", encoding="utf-8")
            state = root / lifecycle.STATE_MANIFEST_PATH
            state.parent.mkdir(parents=True)
            state.write_text(
                explicit_state(
                    "docs/product/plans/archive",
                    ["docs/product/plans/archive/README.md", "docs/product/PLANS_ARCHIVE.md"],
                    active_plan="null",
                ),
                encoding="utf-8",
            )

            result = lifecycle.check_plan_lifecycle(root)

            self.assertFalse(result["success"], result)
            errors = {(item["code"], item["path"]) for item in result["errors"]}
            self.assertIn(("index_missing", "docs/product/plans/archive/README.md"), errors)
            self.assertIn(("index_unmanaged", "docs/product/PLANS_ARCHIVE.md"), errors)

    def test_symbolic_custom_archive_component_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            outside = root / "outside"
            outside.mkdir()
            (root / "docs/product").mkdir(parents=True)
            (root / "docs/product/plans").symlink_to(outside, target_is_directory=True)
            (root / "PLANS.md").write_text(ready_plan(), encoding="utf-8")
            state = root / lifecycle.STATE_MANIFEST_PATH
            state.parent.mkdir(parents=True)
            (root / "docs/codex/README.md").write_text(
                "# Workflow Documentation\n\n"
                f"{lifecycle.INDEX_START}\n"
                "No indexed documents yet.\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            (root / "docs/README.md").write_text(
                "# Documentation\n\n"
                f"{lifecycle.INDEX_START}\n"
                "- [codex/README.md](codex/README.md)\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            state.write_text(
                explicit_state("docs/product/plans/archive", ["docs/product/PLANS_ARCHIVE.md"]),
                encoding="utf-8",
            )

            with self.assertRaises(lifecycle.LifecycleError) as error:
                lifecycle.close_plan(root, "archive")

            self.assertEqual(error.exception.code, "archive_ownership_unsafe")
            self.assertEqual(list(outside.iterdir()), [])

    def test_explicit_compact_closure_clears_active_state_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            plans = root / "PLANS.md"
            plans.write_text(ready_plan(), encoding="utf-8")
            state = root / lifecycle.STATE_MANIFEST_PATH
            state.parent.mkdir(parents=True)
            (root / "docs/codex/README.md").write_text(
                "# Workflow Documentation\n\n"
                f"{lifecycle.INDEX_START}\n"
                "No indexed documents yet.\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            (root / "docs/README.md").write_text(
                "# Documentation\n\n"
                f"{lifecycle.INDEX_START}\n"
                "- [codex/README.md](codex/README.md)\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            state.write_text(
                explicit_state("docs/archive/plans", list(lifecycle.DEFAULT_ARCHIVE_INDEXES)),
                encoding="utf-8",
            )

            result = lifecycle.close_plan(root, "compact")

            self.assertTrue(result["success"], result)
            self.assertIn("active_plan: null", state.read_text(encoding="utf-8"))
            self.assertFalse((root / "docs/archive").exists())
            self.assertTrue(lifecycle.check_plan_lifecycle(root)["success"])

    def test_custom_archive_post_close_failure_rolls_back_plan_indexes_state_and_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "PLANS.md").write_text(ready_plan(), encoding="utf-8")
            state = root / lifecycle.STATE_MANIFEST_PATH
            state.parent.mkdir(parents=True)
            (root / "docs/codex/README.md").write_text(
                "# Workflow Documentation\n\n"
                f"{lifecycle.INDEX_START}\n"
                "No indexed documents yet.\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            (root / "docs/README.md").write_text(
                "# Documentation\n\n"
                f"{lifecycle.INDEX_START}\n"
                "- [codex/README.md](codex/README.md)\n"
                f"{lifecycle.INDEX_END}\n",
                encoding="utf-8",
            )
            state.write_text(
                explicit_state(
                    "docs/product/plans/archive",
                    ["docs/product/PLANS_ARCHIVE.md", "docs/README.md"],
                ),
                encoding="utf-8",
            )
            before_files = {
                path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()
            }
            before_dirs = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())

            with mock.patch.object(
                lifecycle,
                "check_plan_lifecycle",
                return_value={
                    "success": False,
                    "errors": [{"code": "synthetic", "path": "PLANS.md", "detail": "rollback"}],
                    "archive_indexes": {},
                },
            ):
                with self.assertRaises(lifecycle.LifecycleError) as error:
                    lifecycle.close_plan(root, "archive")

            self.assertEqual(error.exception.code, "post_close_validation_failed")
            self.assertEqual(
                {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()},
                before_files,
            )
            self.assertEqual(
                sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir()),
                before_dirs,
            )


if __name__ == "__main__":
    unittest.main()
