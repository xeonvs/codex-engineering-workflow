from __future__ import annotations

import unittest
from pathlib import Path

from test_support import load_script_module

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "skill" / "engineering-workflow" / "assets" / "templates" / "PLANS.md.tmpl"
REFERENCE = REPO_ROOT / "skill" / "engineering-workflow" / "references" / "planning_and_backlog.md"
SKILL = REPO_ROOT / "skill" / "engineering-workflow" / "SKILL.md"
common = load_script_module("common")


class PlanningContractTests(unittest.TestCase):
    def test_full_template_schema_is_structurally_valid(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertEqual(common.validate_plan_schema(text), [])
        for section in common.REQUIRED_PLAN_SECTIONS:
            self.assertIn(f"### {section}", text)

    def test_requirement_id_maps_to_work_queue(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("REQ-001", text)
        self.assertRegex(text, r"WQ-01.*REQ-001")

    def test_missing_requirement_mapping_is_rejected(self):
        text = TEMPLATE.read_text(encoding="utf-8").replace(
            "- [ ] WQ-01 — Implement and validate REQ-001.",
            "- [ ] WQ-01 — Implement the next item.",
        )
        issues = common.validate_plan_schema(text)
        self.assertTrue(any("work queue does not cover REQ-001" in item for item in issues))

    def test_declared_external_source_must_be_preserved(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        issues = common.validate_plan_schema(text, declared_external_sources=True)
        self.assertTrue(any("external sources" in item for item in issues))

    def test_missing_user_decision_section_is_rejected(self):
        text = TEMPLATE.read_text(encoding="utf-8").replace(
            "### User Decisions And Answers",
            "### Decision Notes",
        )
        issues = common.validate_plan_schema(text)
        self.assertTrue(any("User Decisions And Answers" in item for item in issues))

    def test_compressed_or_empty_queue_is_rejected(self):
        text = TEMPLATE.read_text(encoding="utf-8").replace(
            "- [ ] WQ-01 — Implement and validate REQ-001.",
            "- Finish it.",
        )
        issues = common.validate_plan_schema(text)
        self.assertTrue(any("work queue does not cover" in item or "compressed" in item for item in issues))

    def test_resume_point_must_match_first_unfinished_item(self):
        text = TEMPLATE.read_text(encoding="utf-8").replace(
            "Start with WQ-01, the first unfinished queue item.",
            "Start with WQ-09.",
        )
        issues = common.validate_plan_schema(text)
        self.assertTrue(any("Resume Point" in item and "WQ-01" in item for item in issues))

    def test_fidelity_gate_can_require_all_checks_passed(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        issues = common.validate_plan_schema(text, require_fidelity_passed=True)
        self.assertIn("Plan Fidelity Check has unchecked conditions", issues)

    def test_materialization_markers_cover_plan_mode_and_direct_execution(self):
        reference = REFERENCE.read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")
        for marker in (
            "plan_mode_exit_materialization: required",
            "direct_execution_materialization: required",
            "repo_change_plan: full_required",
        ):
            self.assertIn(marker, reference)
            self.assertIn(marker, skill)
        self.assertIn("Plan Mode is one possible plan source, not a prerequisite", reference)

    def test_continuity_and_recovery_have_distinct_reconciliation_scopes(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("## Continuity And Recovery Reconciliation", text)
        self.assertIn("ordinary milestone or subagent return", text)
        self.assertIn("does not require rereading the entire plan", text)
        self.assertIn("actual context compaction that lost material task context", text)
        self.assertIn("inspect current repository state", text)
        self.assertIn("relevant durable artifacts", text)
        self.assertIn("do not reconstruct the complete chat or execution trajectory", text)
        self.assertIn("interruption with uncertain outcome", text)
        self.assertIn("handoff to another root", text)
        self.assertIn("never repeat a side-effecting action blindly", text)
        for status in ("active", "ready_for_closure", "done", "in_progress", "blocked", "out_of_scope"):
            self.assertIn(f"`{status}`", text)

    def test_transient_evidence_and_durable_knowledge_have_distinct_owners(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("## Evidence And Durable Knowledge", text)
        self.assertIn("raw command output", text)
        self.assertIn("large test logs as transient evidence", text)
        self.assertIn("user constraints", text)
        self.assertIn("ordered remaining work as durable knowledge", text)
        self.assertIn("Do not create a repository artifact merely to retain every transient observation", text)
        self.assertIn("Bound output before it enters root context", text)
        self.assertIn("instead of replaying the whole output", text)

    def test_current_state_updates_are_event_driven_not_periodic(self):
        reference = REFERENCE.read_text(encoding="utf-8")
        template = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("not through a separate periodic plan-maintenance loop", reference)
        self.assertIn("do not rewrite the plan", reference)
        self.assertIn("new verified fact supersedes", reference)
        self.assertIn("do not add activity-only rewrites", template)
        self.assertIn("do not restate the whole plan", template)

    def test_stale_completed_state_is_behaviorally_detected(self):
        text = """# Execution Plans

## Recently Completed

- Completed work. Resume from WQ-02 tomorrow.
"""
        issues = common.find_stale_completed_state(text)
        self.assertTrue(any("resume_instruction" in item for item in issues))

    def test_explicit_follow_up_link_is_allowed_in_completed_state(self):
        text = """# Execution Plans

## Recently Completed

- Completed work; explicit follow-up: docs/codex/TASKS_BACKLOG.md.
"""
        self.assertEqual(common.find_stale_completed_state(text), [])


if __name__ == "__main__":
    unittest.main()
