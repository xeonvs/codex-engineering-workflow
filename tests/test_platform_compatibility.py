from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE = REPO_ROOT / "skill/engineering-workflow/references/platform_compatibility.md"
SKILL = REPO_ROOT / "skill/engineering-workflow/SKILL.md"
README = REPO_ROOT / "README.md"


class PlatformCompatibilityTests(unittest.TestCase):
    def test_claude_mode_reads_agents_and_excludes_codex_only_capabilities(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("explicitly read the target repository's applicable root and nested `AGENTS.md`", text)
        self.assertIn("Do not claim that Claude Code automatically discovers", text)
        self.assertIn("orchestrate tools through direct Claude Code calls", text)
        self.assertIn("do not load or apply Codex model profiles", text)
        self.assertIn("Programmatic Tool Calling", text)
        self.assertIn("do not mutate Codex runtime configuration", text)

    def test_shared_skill_routes_platform_before_other_work(self):
        text = SKILL.read_text(encoding="utf-8")
        platform_step = text.index("Read `references/platform_compatibility.md`")
        audit_step = text.index("Run `scripts/repo_audit.py`")
        self.assertLess(platform_step, audit_step)
        self.assertIn("in Claude Code use direct calls", text)

    def test_readme_documents_both_marketplace_flows_and_namespaced_invocation(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("codex plugin marketplace add xeonvs/codex-engineering-workflow", text)
        self.assertIn("claude plugin marketplace add xeonvs/codex-engineering-workflow", text)
        self.assertIn("/engineering-workflow:engineering-workflow", text)
        self.assertIn("claude plugin update engineering-workflow@xeonvs-engineering", text)
        self.assertIn("| Programmatic Tool Calling for eligible bounded stages |", text)


if __name__ == "__main__":
    unittest.main()
