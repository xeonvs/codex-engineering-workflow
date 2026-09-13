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

    def test_shared_skill_preserves_host_selection_before_scoped_audit(self):
        text = SKILL.read_text(encoding="utf-8")
        platform_step = text.index("Read `references/platform_compatibility.md`")
        audit_step = text.index("run `scripts/repo_audit.py`")
        self.assertLess(platform_step, audit_step)
        self.assertIn("select a Codex or Claude Code branch only when the actual host establishes it", text)
        self.assertIn(
            "in Claude Code or another host without that capability use the existing direct/sequential path", text
        )

    def test_other_host_uses_shared_contract_without_foreign_capabilities(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("## Other Or Unestablished Host", text)
        self.assertIn("actual invoking host is neither established as Codex nor established as Claude Code", text)
        self.assertIn("host's native instruction hierarchy and available tools", text)
        self.assertIn("Do not load Codex model profiles", text)
        self.assertIn("apply Claude-specific discovery semantics", text)
        self.assertIn("not a claim that this repository has tested", text)

    def test_readme_documents_both_marketplace_flows_and_namespaced_invocation(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("codex plugin marketplace add xeonvs/codex-engineering-workflow", text)
        self.assertIn("claude plugin marketplace add xeonvs/codex-engineering-workflow", text)
        self.assertIn("/engineering-workflow:engineering-workflow", text)
        self.assertIn("claude plugin update engineering-workflow@xeonvs-engineering", text)
        self.assertIn("| Programmatic Tool Calling for eligible bounded stages |", text)


if __name__ == "__main__":
    unittest.main()
