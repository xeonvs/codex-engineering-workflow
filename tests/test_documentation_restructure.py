from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module

restructure = load_script_module("documentation_restructure")


def active_plan() -> str:
    sections = {
        "Goal": "Move one document without losing navigation or instruction identity.",
        "Plan Origin": "direct_execution",
        "Requested Scope": "Restructure the requested documentation paths.",
        "Requirement Traceability": (
            "| Requirement | Outcome | Status |\n| --- | --- | --- |\n| REQ-001 | Move docs | in_progress |"
        ),
        "Explicit Non-Goals": "No unrelated edits.",
        "Constraints": "Preserve exact approved output.",
        "Inputs And Sources": "User-approved local proposal.",
        "User Decisions And Answers": "The exact proposal is authoritative.",
        "Completed Baseline State": "- [x] Baseline inspected.",
        "Current Work Queue": "- [ ] WQ-01 - Apply REQ-001. `in_progress`",
        "Locked Decisions": "Do not synthesize prose.",
        "Verification": "Check links, anchors, invariants, and rollback.",
        "Latest Validation Results": "Preparation pending.",
        "Risks And Recovery": "Restore exact original bytes on failure.",
        "Resume Point": "Continue WQ-01 with exact proposal preparation.",
        "Plan Fidelity Check": "- [x] Requirements and validation are complete.",
        "Reconciliation Check": "- [ ] Reconcile after apply.",
        "Closure Gate": "- [ ] Close only after validation.",
        "Post-Close Delivery": "Out of scope.",
        "Handoff Notes": "Root retains workflow state ownership.",
    }
    body = "\n\n".join(f"### {heading}\n\n{text}" for heading, text in sections.items())
    return (
        "# Execution Plans\n\nplan_schema_version: 2\n\n"
        "## Active Plan: Documentation Move\n\nStatus: active\n\n"
        f"{body}\n"
    )


def make_target(root: Path) -> None:
    (root / "PLANS.md").write_text(active_plan(), encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    (docs / "old.md").write_text(
        '<!-- ew:invariant id="docs.policy" -->\n# Old Policy\n\nStable domain text.\n',
        encoding="utf-8",
    )
    (docs / "README.md").write_text("# Documentation\n\n- [Policy](old.md#old-policy)\n", encoding="utf-8")


def proposal() -> dict:
    return {
        "schema_version": 1,
        "scope_roots": ["docs"],
        "writes": {
            "docs/old.md": None,
            "docs/policy.md": '<!-- ew:invariant id="docs.policy" -->\n# Policy\n\nStable domain text.\n',
            "docs/README.md": "# Documentation\n\n- [Policy](policy.md#policy)\n",
        },
        "path_map": {"docs/old.md": "docs/policy.md"},
        "anchor_map": {"docs/old.md#old-policy": "docs/policy.md#policy"},
        "compatibility": {
            "docs/old.md": {
                "strategy": "updated_links",
                "target": "docs/policy.md",
                "rationale": "The only incoming link is updated in the same exact proposal.",
            }
        },
        "retired_invariants": {},
    }


def route(owner: str) -> str:
    return f'<!-- ew:route id="policy" triggers="src/**" owners="{owner}" guards="manual_review:policy" -->\n'


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


class DocumentationRestructureTests(unittest.TestCase):
    def test_rendered_heading_keeps_inline_code_in_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            proposed["writes"]["docs/policy.md"] = proposed["writes"]["docs/policy.md"].replace(
                "# Policy", "# Use `tool`"
            )
            proposed["writes"]["docs/README.md"] = "# Documentation\n\n- [Policy](policy.md#use-tool)\n"
            proposed["anchor_map"]["docs/old.md#old-policy"] = "docs/policy.md#use-tool"
            prepared = restructure.prepare_restructure(root, proposed)
            self.assertTrue(prepared["success"], prepared)
            applied = restructure.apply_restructure(root, proposed, prepared["approval_token"])
            self.assertTrue(applied["success"], applied)

    def test_anchor_parser_ignores_code_and_numbers_only_real_headings(self):
        text = "# Repeat\n\n```markdown\n# Repeat\n```\n\n# Repeat\n\n# Alpha `ignored code`\n"
        self.assertEqual(restructure._anchors(text), {"repeat", "repeat-1", "alpha-ignored-code"})

    def test_prepare_is_read_only_and_exact_token_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            before = snapshot(root)

            prepared = restructure.prepare_restructure(root, proposal())
            self.assertTrue(prepared["success"], prepared)
            self.assertRegex(prepared["approval_token"], r"^documentation-restructure-v1:[0-9a-f]{64}$")
            self.assertEqual(snapshot(root), before)

            absent = restructure.apply_restructure(root, proposal(), None)
            self.assertFalse(absent["success"])
            self.assertEqual(absent["status"], "approval_required")
            self.assertEqual(absent["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

    def test_safe_approved_move_applies_exact_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            receipt = restructure.prepare_restructure(root, proposed)["approval_token"]

            result = restructure.apply_restructure(root, proposed, receipt)

            self.assertTrue(result["success"], result)
            self.assertEqual(result["status"], "applied")
            self.assertFalse((root / "docs/old.md").exists())
            self.assertEqual(
                (root / "docs/policy.md").read_text(encoding="utf-8"),
                proposed["writes"]["docs/policy.md"],
            )
            self.assertEqual(
                (root / "docs/README.md").read_text(encoding="utf-8"),
                proposed["writes"]["docs/README.md"],
            )
            self.assertIn("PLANS.md", result["input_snapshot"])

    def test_stale_token_after_input_or_proposal_drift_has_zero_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            receipt = restructure.prepare_restructure(root, proposed)["approval_token"]
            (root / "docs/README.md").write_text(
                "# Documentation\n\nRepository owner changed this file.\n- [Policy](old.md#old-policy)\n",
                encoding="utf-8",
            )
            before = snapshot(root)

            drifted_input = restructure.apply_restructure(root, proposed, receipt)
            self.assertEqual(drifted_input["status"], "stale_approval")
            self.assertEqual(drifted_input["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            receipt = restructure.prepare_restructure(root, proposed)["approval_token"]
            changed_proposal = copy.deepcopy(proposed)
            changed_proposal["writes"]["docs/policy.md"] += "\nNew unapproved text.\n"
            before = snapshot(root)

            drifted_proposal = restructure.apply_restructure(root, changed_proposal, receipt)
            self.assertEqual(drifted_proposal["status"], "stale_approval")
            self.assertEqual(drifted_proposal["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

    def test_incoming_link_anchor_and_invariant_failures_block_before_mutation(self):
        cases: list[tuple[str, dict, str]] = []
        incoming = proposal()
        incoming["writes"]["docs/README.md"] = "# Documentation\n\n- [Policy](old.md#old-policy)\n"
        cases.append(("incoming", incoming, "incoming_link_not_updated"))

        anchor = proposal()
        anchor["writes"]["docs/policy.md"] = '<!-- ew:invariant id="docs.policy" -->\n# Different\n'
        cases.append(("anchor", anchor, "missing_mapped_anchor"))

        unmapped_anchor = proposal()
        unmapped_anchor["anchor_map"] = {}
        cases.append(("unmapped_anchor", unmapped_anchor, "anchor_removed_without_map"))

        invariant = proposal()
        invariant["writes"]["docs/policy.md"] = "# Policy\n\nStable domain text.\n"
        cases.append(("invariant", invariant, "invariant_removed"))

        for name, proposed, expected_code in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_target(root)
                before = snapshot(root)
                prepared = restructure.prepare_restructure(root, proposed)
                self.assertFalse(prepared["success"])
                self.assertIn(expected_code, {issue["code"] for issue in prepared["issues"]})
                result = restructure.apply_restructure(root, proposed, prepared["approval_token"])
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["mutation_log"], [])
                self.assertEqual(snapshot(root), before)

    def test_in_place_existing_document_anchor_requires_preservation_or_explicit_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = {
                "schema_version": 1,
                "scope_roots": ["docs"],
                "writes": {
                    "docs/old.md": '<!-- ew:invariant id="docs.policy" -->\n# Renamed\n\nStable domain text.\n',
                    "docs/README.md": "# Documentation\n\n- [Policy](old.md#renamed)\n",
                },
                "path_map": {},
                "anchor_map": {},
                "compatibility": {},
                "retired_invariants": {},
            }

            blocked = restructure.prepare_restructure(root, proposed)
            self.assertFalse(blocked["success"])
            self.assertIn("anchor_removed_without_map", {issue["code"] for issue in blocked["issues"]})

            proposed["anchor_map"] = {"docs/old.md#old-policy": "docs/old.md#renamed"}
            prepared = restructure.prepare_restructure(root, proposed)
            self.assertTrue(prepared["success"], prepared)

    def test_explicit_retirement_and_privacy_are_separate_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            proposed["writes"]["docs/policy.md"] = "# Policy\n\nStable domain text.\n"
            proposed["retired_invariants"] = {
                "docs.policy": "The policy is intentionally retired by the approved restructure."
            }
            prepared = restructure.prepare_restructure(root, proposed)
            self.assertTrue(prepared["success"], prepared)

            proposed["writes"]["docs/policy.md"] += "/" + "Users" + "/developer/private-note\n"
            private = restructure.prepare_restructure(root, proposed)
            self.assertFalse(private["success"])
            self.assertTrue(private["privacy_findings"])
            self.assertNotIn("developer/private-note", repr(private["privacy_findings"]))
            result = restructure.apply_restructure(root, proposed, private["approval_token"])
            self.assertEqual(result["status"], "privacy_blocked")
            self.assertEqual(result["mutation_log"], [])

    def test_symlink_root_and_parent_are_rejected_without_outside_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            actual = base / "actual"
            actual.mkdir()
            make_target(actual)
            linked = base / "linked"
            linked.symlink_to(actual, target_is_directory=True)
            result = restructure.prepare_restructure(linked, proposal())
            self.assertFalse(result["success"])
            self.assertEqual(result["issues"][0]["code"], "unsafe_repository_root")

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "repo"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "PLANS.md").write_text(active_plan(), encoding="utf-8")
            (root / "docs").symlink_to(outside, target_is_directory=True)
            result = restructure.prepare_restructure(root, proposal())
            self.assertFalse(result["success"])
            self.assertIn(result["issues"][0]["code"], {"unsafe_target_path", "missing_target_path"})
            self.assertEqual(list(outside.iterdir()), [])

    def test_post_write_failure_rolls_back_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            receipt = restructure.prepare_restructure(root, proposed)["approval_token"]
            before = snapshot(root)

            with mock.patch.object(
                restructure,
                "_post_write_validate",
                return_value=[{"code": "induced_validation_failure"}],
            ):
                result = restructure.apply_restructure(root, proposed, receipt)

            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "rolled_back")
            self.assertEqual(result["rollback_errors"], [])
            self.assertEqual(snapshot(root), before)

    def test_first_write_failure_without_mutation_leaves_every_path_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            receipt = restructure.prepare_restructure(root, proposed)["approval_token"]
            before = snapshot(root)

            with mock.patch.object(restructure._SecureRoot, "write_text", side_effect=OSError("induced failure")):
                result = restructure.apply_restructure(root, proposed, receipt)

            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "rolled_back")
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual(result["rollback_errors"], [])
            self.assertEqual(snapshot(root), before)

    def test_concurrent_edit_of_attempted_path_is_preserved_as_recovery_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            receipt = restructure.prepare_restructure(root, proposed)["approval_token"]
            concurrent = b"# Concurrent owner edit\n"

            def edit_attempted_path_then_fail(_secure_root, relative, _text):
                (root / relative).write_bytes(concurrent)
                raise OSError("induced failure after concurrent edit")

            with mock.patch.object(restructure._SecureRoot, "write_text", new=edit_attempted_path_then_fail):
                result = restructure.apply_restructure(root, proposed, receipt)

            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "rollback_failed")
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual((root / "docs/README.md").read_bytes(), concurrent)
            self.assertIn("recovery_conflict", {error["error"] for error in result["rollback_errors"]})

    def test_concurrent_edit_of_unattempted_proposal_path_is_preserved_as_recovery_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            receipt = restructure.prepare_restructure(root, proposed)["approval_token"]
            concurrent = b"# Concurrent edit of old path\n"

            def edit_other_path_then_fail(_secure_root, _relative, _text):
                (root / "docs/old.md").write_bytes(concurrent)
                raise OSError("induced failure after concurrent edit")

            with mock.patch.object(restructure._SecureRoot, "write_text", new=edit_other_path_then_fail):
                result = restructure.apply_restructure(root, proposed, receipt)

            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "rollback_failed")
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual((root / "docs/old.md").read_bytes(), concurrent)
            self.assertIn("recovery_conflict", {error["error"] for error in result["rollback_errors"]})

    def test_restore_failure_reports_recovery_snapshot_without_claiming_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            proposed = proposal()
            receipt = restructure.prepare_restructure(root, proposed)["approval_token"]
            original_write_bytes = restructure._SecureRoot.write_bytes

            def fail_old_restore(secure_root, relative, data):
                if relative == "docs/old.md":
                    raise OSError("induced restore failure")
                return original_write_bytes(secure_root, relative, data)

            with (
                mock.patch.object(
                    restructure,
                    "_post_write_validate",
                    return_value=[{"code": "induced_validation_failure"}],
                ),
                mock.patch.object(restructure._SecureRoot, "write_bytes", new=fail_old_restore),
            ):
                result = restructure.apply_restructure(root, proposed, receipt)

            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "rollback_failed")
            self.assertTrue(result["rollback_errors"])
            self.assertTrue(result["recovery"]["required"])
            self.assertEqual(result["recovery"]["expected_original_snapshot"]["docs/old.md"]["state"], "file")

    def test_plan_must_already_be_full_active_and_cannot_be_proposed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            (root / "PLANS.md").write_text("# compressed\n", encoding="utf-8")
            before = snapshot(root)
            result = restructure.apply_restructure(root, proposal(), "not-an-approval")
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

        forbidden = proposal()
        forbidden["scope_roots"] = ["."]
        forbidden["writes"]["PLANS.md"] = active_plan()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            prepared = restructure.prepare_restructure(root, forbidden)
            self.assertFalse(prepared["success"])
            self.assertEqual(prepared["issues"][0]["code"], "shared_state_write_forbidden")

    def test_invalid_plan_diagnostics_do_not_echo_source_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            sentinel = "private-origin-sentinel"
            plan = (root / "PLANS.md").read_text(encoding="utf-8")
            (root / "PLANS.md").write_text(plan.replace("direct_execution", sentinel), encoding="utf-8")

            report = restructure.prepare_restructure(root, proposal())

            self.assertTrue(report["success"], report)
            self.assertFalse(report["plan_requirement"]["satisfied"])
            self.assertNotIn(sentinel, repr(report))
            self.assertIn(
                "plan_origin_invalid", {issue.get("reason") for issue in report["plan_requirement"]["issues"]}
            )

    def test_prepare_without_plan_is_read_only_and_apply_requires_fresh_plan_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            (root / "PLANS.md").unlink()
            before = snapshot(root)
            proposed = proposal()

            prepared = restructure.prepare_restructure(root, proposed)
            self.assertTrue(prepared["success"], prepared)
            self.assertFalse(prepared["plan_requirement"]["satisfied"])
            self.assertEqual(prepared["input_snapshot"]["PLANS.md"]["state"], "missing")
            self.assertEqual(snapshot(root), before)

            blocked = restructure.apply_restructure(root, proposed, prepared["approval_token"])
            self.assertEqual(blocked["status"], "blocked")
            self.assertIn("active_plan_required", {issue["code"] for issue in blocked["issues"]})
            self.assertEqual(blocked["mutation_log"], [])
            self.assertEqual(snapshot(root), before)

            (root / "PLANS.md").write_text(active_plan(), encoding="utf-8")
            with_plan = snapshot(root)
            stale = restructure.apply_restructure(root, proposed, prepared["approval_token"])
            self.assertEqual(stale["status"], "stale_approval")
            self.assertEqual(snapshot(root), with_plan)
            fresh = restructure.prepare_restructure(root, proposed)
            self.assertTrue(fresh["plan_requirement"]["satisfied"])
            applied = restructure.apply_restructure(root, proposed, fresh["approval_token"])
            self.assertTrue(applied["success"], applied)

    def test_root_and_nested_route_owners_require_explicit_rewrites_and_valid_anchors(self):
        for source in ("AGENTS.md", "docs/AGENTS.md"):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_target(root)
                (root / source).write_text(route("docs/old.md#old-policy"), encoding="utf-8")
                proposed = proposal()
                before = snapshot(root)

                blocked = restructure.prepare_restructure(root, proposed)
                self.assertFalse(blocked["success"])
                self.assertIn("broken_instruction_dependency", {issue["code"] for issue in blocked["issues"]})
                self.assertIn(source, blocked["input_snapshot"])
                self.assertEqual(snapshot(root), before)

                proposed["scope_roots"].append(source)
                proposed["writes"][source] = route("docs/policy.md#missing-anchor")
                anchor = restructure.prepare_restructure(root, proposed)
                self.assertFalse(anchor["success"])
                self.assertIn("missing_route_owner_anchor", {issue["code"] for issue in anchor["issues"]})

                proposed["writes"][source] = route("docs/policy.md#policy")
                prepared = restructure.prepare_restructure(root, proposed)
                self.assertTrue(prepared["success"], prepared)
                result = restructure.apply_restructure(root, proposed, prepared["approval_token"])
                self.assertTrue(result["success"], result)
                self.assertEqual((root / source).read_text(), proposed["writes"][source])

    def test_route_sources_and_resolved_local_owner_bytes_bind_approval(self):
        for changed in ("AGENTS.md", "docs/AGENTS.md", "rules/writing.md"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_target(root)
                (root / "rules").mkdir()
                (root / "rules/writing.md").write_text("# Writing\n\n# Alternate\n", encoding="utf-8")
                for source in ("AGENTS.md", "docs/AGENTS.md"):
                    (root / source).write_text(
                        route(
                            "rules/writing.md#writing|skill://engineering-workflow/references/documentation_navigation.md"
                        ),
                        encoding="utf-8",
                    )
                prepared = restructure.prepare_restructure(root, proposal())
                self.assertTrue(prepared["success"], prepared)
                for dependency in ("AGENTS.md", "docs/AGENTS.md", "rules/writing.md"):
                    self.assertIn(dependency, prepared["input_snapshot"])
                self.assertFalse(any(path.startswith("skill://") for path in prepared["input_snapshot"]))

                if changed.endswith("AGENTS.md"):
                    source_text = (root / changed).read_text(encoding="utf-8")
                    (root / changed).write_text(source_text.replace("#writing|", "#alternate|"), encoding="utf-8")
                else:
                    with (root / changed).open("a", encoding="utf-8") as handle:
                        handle.write("\nUpdated owner evidence.\n")
                before = snapshot(root)
                current = restructure.prepare_restructure(root, proposal())
                self.assertTrue(current["success"], current)
                self.assertNotEqual(current["approval_token"], prepared["approval_token"])
                stale = restructure.apply_restructure(root, proposal(), prepared["approval_token"])
                self.assertEqual(stale["status"], "stale_approval")
                self.assertEqual(stale["mutation_log"], [])
                self.assertEqual(snapshot(root), before)

    def test_state_file_paths_require_explicit_rewrites_and_bind_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            state_path = restructure.STATE_MANIFEST_PATH
            (root / state_path).parent.mkdir(parents=True)
            original_state = "managed_paths:\n  - docs/old.md\nshared_paths:\n  - PLANS.md\nprotected_paths: []\n"
            (root / state_path).write_text(original_state, encoding="utf-8")
            proposed = proposal()
            before = snapshot(root)

            blocked = restructure.prepare_restructure(root, proposed)
            self.assertFalse(blocked["success"])
            self.assertIn("broken_instruction_dependency", {issue["code"] for issue in blocked["issues"]})
            self.assertEqual(snapshot(root), before)

            proposed["writes"][state_path] = original_state.replace("docs/old.md", "docs/policy.md")
            prepared = restructure.prepare_restructure(root, proposed)
            self.assertTrue(prepared["success"], prepared)
            self.assertIn(state_path, prepared["input_snapshot"])
            (root / state_path).write_text(original_state + "# Owner changed state.\n", encoding="utf-8")
            before = snapshot(root)
            stale = restructure.apply_restructure(root, proposed, prepared["approval_token"])
            self.assertEqual(stale["status"], "stale_approval")
            self.assertEqual(snapshot(root), before)
            refreshed = restructure.prepare_restructure(root, proposed)
            result = restructure.apply_restructure(root, proposed, refreshed["approval_token"])
            self.assertTrue(result["success"], result)
            self.assertEqual((root / state_path).read_text(), proposed["writes"][state_path])

    def test_declared_state_owner_bytes_and_invalid_path_lists_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            state_path = restructure.STATE_MANIFEST_PATH
            (root / state_path).parent.mkdir(parents=True)
            (root / "docs/local-owner.md").write_text("# Local owner\n", encoding="utf-8")
            (root / state_path).write_text("protected_paths:\n  - docs/local-owner.md\n", encoding="utf-8")
            prepared = restructure.prepare_restructure(root, proposal())
            self.assertTrue(prepared["success"], prepared)
            self.assertIn("docs/local-owner.md", prepared["input_snapshot"])
            (root / "docs/local-owner.md").write_text("# Updated local owner\n", encoding="utf-8")
            stale = restructure.apply_restructure(root, proposal(), prepared["approval_token"])
            self.assertEqual(stale["status"], "stale_approval")
            self.assertEqual(stale["mutation_log"], [])

            (root / state_path).write_text("protected_paths:\n  - ../outside.md\n", encoding="utf-8")
            invalid = restructure.prepare_restructure(root, proposal())
            self.assertFalse(invalid["success"])
            self.assertIn("invalid_state_paths", {issue["code"] for issue in invalid["issues"]})

    def test_fresh_upgraded_target_preserves_lazy_archive_missing_snapshot(self):
        migrator = load_script_module("upgrade_target_workflow")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Target\n", encoding="utf-8")
            upgraded = migrator.apply_migration(root, "0.10.0")
            self.assertTrue(upgraded["success"], upgraded)
            (root / "PLANS.md").write_text(active_plan(), encoding="utf-8")
            domain = root / "docs/domain"
            domain.mkdir()
            (domain / "old.md").write_text(
                '<!-- ew:invariant id="docs.policy" -->\n# Old Policy\n\nStable domain text.\n',
                encoding="utf-8",
            )
            (domain / "README.md").write_text("# Documentation\n\n- [Policy](old.md#old-policy)\n", encoding="utf-8")
            proposed = proposal()
            proposed["writes"] = {
                path.replace("docs/", "docs/domain/", 1): text for path, text in proposed["writes"].items()
            }
            proposed["path_map"] = {"docs/domain/old.md": "docs/domain/policy.md"}
            proposed["anchor_map"] = {"docs/domain/old.md#old-policy": "docs/domain/policy.md#policy"}
            proposed["compatibility"] = {
                "docs/domain/old.md": {**proposed["compatibility"]["docs/old.md"], "target": "docs/domain/policy.md"}
            }
            lazy_paths = ("docs/archive/README.md", "docs/archive/plans/README.md")
            for path in lazy_paths:
                self.assertFalse((root / path).exists())
            before = snapshot(root)

            prepared = restructure.prepare_restructure(root, proposed)
            self.assertTrue(prepared["success"], prepared)
            for path in lazy_paths:
                self.assertEqual(prepared["input_snapshot"][path]["state"], "missing")
                self.assertIn(path, prepared["unchanged_missing_state_paths"])
            self.assertEqual(snapshot(root), before)
            applied = restructure.apply_restructure(root, proposed, prepared["approval_token"])
            self.assertTrue(applied["success"], applied)
            for path in lazy_paths:
                self.assertFalse((root / path).exists())

    def test_new_missing_state_declaration_is_not_treated_as_lazy_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            state_path = restructure.STATE_MANIFEST_PATH
            (root / state_path).parent.mkdir(parents=True)
            original_state = (
                "managed_paths:\n  - docs/archive/README.md\nplan_archive_indexes:\n  - docs/archive/README.md\n"
            )
            (root / state_path).write_text(original_state, encoding="utf-8")
            proposed = proposal()
            unchanged = restructure.prepare_restructure(root, proposed)
            self.assertTrue(unchanged["success"], unchanged)
            self.assertIn("docs/archive/README.md", unchanged["unchanged_missing_state_paths"])

            proposed["writes"][state_path] = original_state.replace(
                "managed_paths:\n", "managed_paths:\n  - docs/new-missing.md\n"
            )
            blocked = restructure.prepare_restructure(root, proposed)
            self.assertFalse(blocked["success"])
            self.assertIn({"code": "broken_instruction_dependency", "path": "docs/new-missing.md"}, blocked["issues"])

    def test_symbolic_route_sources_and_local_owners_do_not_escape_target(self):
        for symbolic_source in (False, True):
            with self.subTest(symbolic_source=symbolic_source), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                root = base / "target"
                root.mkdir()
                make_target(root)
                outside = base / "outside.md"
                outside.write_text("# Outside\n", encoding="utf-8")
                if symbolic_source:
                    (root / "docs/AGENTS.md").symlink_to(outside)
                else:
                    (root / "AGENTS.md").write_text(route("docs/local-owner.md"), encoding="utf-8")
                    (root / "docs/local-owner.md").symlink_to(outside)
                before = snapshot(root)
                result = restructure.prepare_restructure(root, proposal())
                self.assertFalse(result["success"])
                self.assertIn("unsafe_target_path", {issue["code"] for issue in result["issues"]})
                self.assertEqual(snapshot(root), before)
                self.assertEqual(outside.read_text(), "# Outside\n")

    def test_html_and_reference_incoming_links_require_rewrites_and_bind_snapshot(self):
        incoming_styles = {
            "html": lambda destination: f'# Incoming\n\n<a href="{destination}">Policy</a>\n',
            "reference": lambda destination: f"# Incoming\n\n[Policy][owner]\n\n[owner]: {destination}\n",
            "collapsed_reference": lambda destination: f"# Incoming\n\n[Policy][]\n\n[policy]: {destination}\n",
            "shortcut_reference": lambda destination: f"# Incoming\n\n[Policy]\n\n[policy]: {destination}\n",
            "duplicate_reference": lambda destination: (
                f"# Incoming\n\n[Policy][owner]\n\n[owner]: {destination}\n[owner]: policy.md#policy\n"
            ),
        }
        for style, incoming in incoming_styles.items():
            with self.subTest(style=style), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_target(root)
                source = "docs/incoming.md"
                (root / source).write_text(incoming("old.md#old-policy"), encoding="utf-8")
                before = snapshot(root)
                proposed = proposal()

                blocked = restructure.prepare_restructure(root, proposed)
                self.assertFalse(blocked["success"])
                self.assertIn("incoming_link_not_updated", {issue["code"] for issue in blocked["issues"]})
                self.assertIn(source, blocked["input_snapshot"])
                result = restructure.apply_restructure(root, proposed, blocked["approval_token"])
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["mutation_log"], [])
                self.assertEqual(snapshot(root), before)

                proposed["writes"][source] = incoming("policy.md#policy")
                prepared = restructure.prepare_restructure(root, proposed)
                self.assertTrue(prepared["success"], prepared)
                result = restructure.apply_restructure(root, proposed, prepared["approval_token"])
                self.assertTrue(result["success"], result)
                self.assertEqual((root / source).read_text(), proposed["writes"][source])

    def test_supported_unrelated_html_decoration_does_not_block_restructure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            decoration = '<p align="center"><img src="unrelated-decoration.svg" alt="Logo" /></p>\n'
            (root / "README.md").write_text(decoration, encoding="utf-8")

            prepared = restructure.prepare_restructure(root, proposal())
            self.assertTrue(prepared["success"], prepared)
            self.assertNotIn("README.md", prepared["input_snapshot"])
            self.assertEqual((root / "README.md").read_text(), decoration)

    def test_unresolved_or_unparsed_references_block_with_bound_source(self):
        for uncertain in (
            '<a href="old.md#old-policy"',
            "[Policy][undefined]",
            "[Policy [nested]](old.md)",
        ):
            with self.subTest(uncertain=uncertain), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_target(root)
                source = "docs/incoming.md"
                (root / source).write_text("# Incoming\n\n" + uncertain + "\n", encoding="utf-8")
                before = snapshot(root)

                blocked = restructure.prepare_restructure(root, proposal())
                self.assertFalse(blocked["success"])
                self.assertIn("unsupported_document_reference", {issue["code"] for issue in blocked["issues"]})
                self.assertIn(source, blocked["input_snapshot"])
                result = restructure.apply_restructure(root, proposal(), blocked["approval_token"])
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["mutation_log"], [])
                self.assertEqual(snapshot(root), before)

    def test_fenced_and_inline_invariant_examples_are_preserved_without_becoming_owners(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            marker = '<!-- ew:invariant id="docs.policy" -->'
            example = "# Examples\n\n```markdown\n" + marker + "\n```\n\n`" + marker + "`\n"
            (root / "docs/example.md").write_text(example, encoding="utf-8")
            proposed = proposal()

            prepared = restructure.prepare_restructure(root, proposed)
            self.assertTrue(prepared["success"], prepared)
            result = restructure.apply_restructure(root, proposed, prepared["approval_token"])
            self.assertTrue(result["success"], result)
            self.assertEqual((root / "docs/example.md").read_text(), example)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_target(root)
            (root / "docs/duplicate.md").write_text(marker + "\n# Another owner\n", encoding="utf-8")
            prepared = restructure.prepare_restructure(root, proposal())
            self.assertFalse(prepared["success"])
            self.assertIn("duplicate_invariant", {issue["code"] for issue in prepared["issues"]})


if __name__ == "__main__":
    unittest.main()
