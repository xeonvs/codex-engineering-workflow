from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE = REPO_ROOT / "skill" / "engineering-workflow" / "references" / "agent_orchestration.md"
PROFILES = REPO_ROOT / "skill" / "engineering-workflow" / "references" / "model_profiles.md"
AGENTS = REPO_ROOT / "skill" / "engineering-workflow" / "assets" / "agents"


class AgentOrchestrationTests(unittest.TestCase):
    def test_deterministic_polling_is_not_routed_to_a_model(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("## Deterministic Route", text)
        self.assertIn("Do not use a language-model subagent", text)
        self.assertIn("sleep", text)
        self.assertIn("polling", text)
        self.assertIn("Do not implement monitoring as a model sleep loop", text)

    def test_root_owns_shared_state_and_final_synthesis(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("final synthesis", text)
        self.assertIn("Only the root agent writes", text)
        self.assertIn("`PLANS.md`", text)
        self.assertIn("workflow state manifest", text)
        self.assertIn("single-writer", text)

    def test_fanout_depth_and_recursive_delegation_are_bounded(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("two or three genuinely independent agents", text)
        self.assertIn("agents.max_depth = 1", text)
        self.assertIn("recursive delegation", text)
        self.assertIn("Do not consume every available thread", text)

    def test_subagent_contract_has_all_required_boundaries(self):
        text = REFERENCE.read_text(encoding="utf-8")
        for field in (
            "scope",
            "inputs",
            "allowed paths",
            "permissions",
            "model profile",
            "output schema",
            "stopping condition",
            "escalation condition",
            "retry budget",
        ):
            self.assertIn(field, text)

    def test_optional_profiles_use_expected_safety_defaults(self):
        utility = tomllib.loads((AGENTS / "utility.toml.tmpl").read_text(encoding="utf-8"))
        explorer = tomllib.loads((AGENTS / "explorer.toml.tmpl").read_text(encoding="utf-8"))
        reviewer = tomllib.loads((AGENTS / "reviewer.toml.tmpl").read_text(encoding="utf-8"))
        self.assertEqual(utility["model"], "gpt-" + "5.6-" + "terra")
        self.assertEqual(utility["model_reasoning_effort"], "low")
        self.assertEqual(utility["sandbox_mode"], "read-only")
        self.assertEqual(explorer["sandbox_mode"], "read-only")
        self.assertEqual(reviewer["model_reasoning_effort"], "high")
        self.assertEqual(reviewer["sandbox_mode"], "read-only")

    def test_utility_template_has_no_expensive_reasoning_or_api_pro_fields(self):
        text = (AGENTS / "utility.toml.tmpl").read_text(encoding="utf-8")
        for value in ('"high"', '"xhigh"', '"max"', '"ultra"', "reasoning.mode"):
            self.assertNotIn(value, text)

    def test_minimal_and_none_are_conditional_only(self):
        text = PROFILES.read_text(encoding="utf-8")
        self.assertIn("allow `minimal` or `none` only when", text)
        self.assertIn("regression tests or evaluation preserve quality", text)

    def test_concrete_model_slugs_have_one_reference_owner(self):
        runtime_references = REPO_ROOT / "skill" / "engineering-workflow" / "references"
        owners = []
        for path in runtime_references.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if "gpt-" + "5.6" in text:
                owners.append(path.name)
        self.assertEqual(owners, ["model_profiles.md"])


if __name__ == "__main__":
    unittest.main()
