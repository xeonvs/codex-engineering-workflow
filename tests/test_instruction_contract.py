from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from test_support import load_script_module

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "mature_repo"
contract = load_script_module("instruction_contract")


class InstructionContractTests(unittest.TestCase):
    def _copy_fixture(self, root: Path) -> None:
        shutil.copytree(FIXTURE, root, dirs_exist_ok=True)

    def test_valid_owner_route_incident_guard_graph_passes(self):
        result = contract.check_instruction_contract(FIXTURE)
        self.assertTrue(result["success"], result)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["contract_version"], 3)
        self.assertEqual(result["required_contract_version"], 3)
        self.assertEqual(result["missing_required_invariants"], [])
        self.assertEqual(result["missing_required_routes"], [])
        self.assertEqual(len(result["incidents"]), 4)

    def test_planning_template_routes_custom_archive_closure_by_semantic_trigger(self):
        template = (
            Path(__file__).resolve().parents[1] / "skill/engineering-workflow/assets/templates/AGENTS.md.tmpl"
        ).read_text(encoding="utf-8")
        self.assertIn("workflow-state plan archive", template)
        self.assertIn("plan closure", template)
        self.assertIn("skill://engineering-workflow/references/planning_and_backlog.md", template)

    def test_customized_v1_reports_structured_migration_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            agents = root / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8")
                .replace("instruction_contract_version: 3", "instruction_contract_version: 1")
                .replace(
                    '<!-- ew:route id="long-running-execution" triggers="long-running commands|builds|tests|polling" owners="docs/engineering/project_principles.md" guards="manual_review:verify completion evidence deadline bounded output and task-owned cleanup" -->\n| long-running-execution | long-running local work | `docs/engineering/project_principles.md` | completion evidence review |\n',
                    "",
                ),
                encoding="utf-8",
            )
            principles = root / "docs/engineering/project_principles.md"
            text = principles.read_text(encoding="utf-8")
            marker = '<!-- ew:invariant id="workflow.completion-driven-wait" -->'
            principles.write_text(text[: text.index(marker)].rstrip() + "\n", encoding="utf-8")

            result = contract.check_instruction_contract(root)

            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "instruction_migration_required")
            self.assertEqual(result["contract_version"], 1)
            self.assertEqual(result["missing_required_invariants"], ["workflow.completion-driven-wait"])
            self.assertEqual(result["missing_required_routes"], ["long-running-execution"])

    def test_customized_v2_requires_review_invariant_before_v3_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            agents = root / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8").replace(
                    "instruction_contract_version: 3",
                    "instruction_contract_version: 2",
                ),
                encoding="utf-8",
            )
            principles = root / "docs/engineering/project_principles.md"
            text = principles.read_text(encoding="utf-8")
            marker = '<!-- ew:invariant id="workflow.review-before-commit" -->'
            review_start = text.index(marker)
            wait_start = text.index('<!-- ew:invariant id="workflow.completion-driven-wait" -->', review_start)
            principles.write_text(text[:review_start] + text[wait_start:], encoding="utf-8")

            result = contract.check_instruction_contract(root)

            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "instruction_migration_required")
            self.assertEqual(result["contract_version"], 2)
            self.assertEqual(result["required_contract_version"], 3)
            self.assertEqual(result["missing_required_invariants"], ["workflow.review-before-commit"])

    def test_duplicate_invariant_id_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            path = root / "docs/providers.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + '\n<!-- ew:invariant id="provider.persist-readback" -->\n## Duplicate\n\nDuplicate owner.\n',
                encoding="utf-8",
            )
            result = contract.check_instruction_contract(root)
            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "instruction_conflict")
            self.assertTrue(any(item["code"] == "duplicate_invariant_owner" for item in result["errors"]))

    def test_missing_route_and_guard_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            pitfalls = root / "docs/codex/AGENT_EXECUTION_PITFALLS.md"
            text = pitfalls.read_text(encoding="utf-8").replace("Route: `provider-change`", "Route: `missing-route`", 1)
            text = text.replace("Guard: `test:provider-contract`", "Guard: `remember-it`", 1)
            pitfalls.write_text(text, encoding="utf-8")
            result = contract.check_instruction_contract(root)
            self.assertFalse(result["success"])
            self.assertEqual(result["status"], "guard_missing")
            codes = {item["code"] for item in result["errors"]}
            self.assertIn("guard_missing", codes)
            self.assertIn("route_missing", codes)

    def test_imperative_legacy_pitfall_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            pitfalls = root / "docs/codex/AGENT_EXECUTION_PITFALLS.md"
            pitfalls.write_text(
                pitfalls.read_text(encoding="utf-8") + "\n- Better default: Never add another helper.\n",
                encoding="utf-8",
            )
            result = contract.check_instruction_contract(root)
            self.assertFalse(result["success"])
            self.assertTrue(any(item["code"] == "imperative_incident_field" for item in result["errors"]))

    def test_compact_checked_queue_conflict_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            agents = root / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8") + "\nUse a compact checked queue item for bounded code changes.\n",
                encoding="utf-8",
            )
            result = contract.check_instruction_contract(root)
            self.assertEqual(result["status"], "instruction_conflict")
            self.assertTrue(any(item["code"] == "conflicting_planning_rule" for item in result["errors"]))

    def test_historical_details_are_allowed_in_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            pitfalls = root / "docs/codex/AGENT_EXECUTION_PITFALLS.md"
            pitfalls.write_text(
                pitfalls.read_text(encoding="utf-8").replace(
                    "Evidence: sanitized provider regression fixture.",
                    "Evidence: archived 2026-07-13 release 0.5.1 and selector `#sample`.",
                ),
                encoding="utf-8",
            )
            result = contract.check_instruction_contract(root)
            self.assertTrue(result["success"], result)

    def test_router_cannot_become_a_canonical_rule_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            agents = root / "AGENTS.md"
            agents.write_text(
                agents.read_text(encoding="utf-8")
                + '\n<!-- ew:invariant id="ui.duplicate-owner" -->\n## UI Rule\n\nNever skip rendered QA.\n',
                encoding="utf-8",
            )
            result = contract.check_instruction_contract(root)
            self.assertEqual(result["status"], "instruction_conflict")
            self.assertTrue(any(item["code"] == "router_defines_invariant" for item in result["errors"]))

    def test_ui_route_loads_rendered_acceptance_owner(self):
        result = contract.check_instruction_contract(FIXTURE)
        route = next(item for item in result["routes"] if item["id"] == "ui-change")
        self.assertIn("docs/ui.md", route["owners"])
        self.assertIn("harness:rendered-ui", route["guards"])


if __name__ == "__main__":
    unittest.main()
