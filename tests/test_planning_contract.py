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

    def test_reconciliation_semantics_cover_every_resume_boundary(self):
        text = REFERENCE.read_text(encoding="utf-8")
        for boundary in (
            "context compaction",
            "interruption",
            "resume",
            "milestone closure",
            "subagent handoff",
            "new Codex session",
        ):
            self.assertIn(boundary, text)
        for status in ("done", "in_progress", "blocked", "promoted", "superseded"):
            self.assertIn(f"`{status}`", text)

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
