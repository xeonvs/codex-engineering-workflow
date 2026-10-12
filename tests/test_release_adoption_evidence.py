from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_support import load_script_module

adoption = load_script_module("release_adoption")
SEMANTIC_ID = "documentation-maintenance-v1"
RUNTIME_ID = "stable-skill-update-runtime-v1"


class ReleaseAdoptionEvidenceTests(unittest.TestCase):
    def _target(self, root: Path) -> None:
        (root / "docs/engineering").mkdir(parents=True)
        (root / "docs/codex").mkdir()
        (root / "AGENTS.md").write_text("# Router\n", encoding="utf-8")
        (root / "docs/engineering/project_principles.md").write_text("# Principles\n", encoding="utf-8")

    def _record(self, root: Path, ids=None, evidence=None) -> None:
        ids = ids if ids is not None else [SEMANTIC_ID, RUNTIME_ID]
        text = 'skill_version: "0.10.0"\nadopted_change_ids:\n'
        text += "".join(f"  - {identifier}\n" for identifier in ids)
        if evidence is not None:
            text += "adoption_evidence:\n" + "".join(
                f'  {identifier}: "{digest}"\n' for identifier, digest in evidence.items()
            )
        (root / adoption.STATE_PATH).write_text(text, encoding="utf-8")

    def test_same_version_recorded_ids_require_matching_owner_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            self._record(root)
            initial = adoption.assess_target_adoption(root, "0.10.0")
            self.assertIn(SEMANTIC_ID, initial["pending_change_ids"])
            self.assertIn(RUNTIME_ID, initial["resolved_change_ids"])
            evidence = adoption.adoption_evidence(root, change_ids=[SEMANTIC_ID, RUNTIME_ID])
            self.assertEqual(set(evidence), {SEMANTIC_ID})
            self._record(root, evidence=evidence)
            reviewed = adoption.assess_target_adoption(root, "0.10.0")
            self.assertIn(SEMANTIC_ID, reviewed["resolved_change_ids"])
            self.assertEqual(reviewed["owner_evidence"][SEMANTIC_ID], evidence[SEMANTIC_ID])
            (root / "AGENTS.md").write_text("# Changed router\n", encoding="utf-8")
            drifted = adoption.assess_target_adoption(root, "0.10.0")
            self.assertIn(SEMANTIC_ID, drifted["pending_change_ids"])
            self.assertNotIn(SEMANTIC_ID, drifted["resolved_change_ids"])

    def test_explicit_ids_are_current_review_evidence_even_when_stored_evidence_drifts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            evidence = adoption.adoption_evidence(root)
            self._record(root, evidence=evidence)
            (root / "docs/engineering/project_principles.md").write_text("# New rule\n", encoding="utf-8")
            reviewed = adoption.assess_target_adoption(root, "0.10.0", [SEMANTIC_ID])
            self.assertIn(SEMANTIC_ID, reviewed["resolved_change_ids"])
            self.assertNotEqual(reviewed["owner_evidence"][SEMANTIC_ID], evidence[SEMANTIC_ID])

    def test_writing_owner_drift_and_addition_invalidate_recorded_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            evidence = adoption.adoption_evidence(root, change_ids=[SEMANTIC_ID])
            self._record(root, evidence=evidence)
            owner = root / "docs/engineering/document_writing.md"
            owner.write_text("# Local writing rules\n", encoding="utf-8")
            after_addition = adoption.assess_target_adoption(root, "0.10.0")
            self.assertIn(SEMANTIC_ID, after_addition["pending_change_ids"])
            self._record(root, evidence=after_addition["owner_evidence"])
            owner.write_text("# Different local writing rules\n", encoding="utf-8")
            self.assertIn(SEMANTIC_ID, adoption.assess_target_adoption(root, "0.10.0")["pending_change_ids"])

    def test_custom_route_owner_is_fingerprinted_even_outside_default_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            (root / "manuals").mkdir()
            owner = root / "manuals/style.md"
            owner.write_text("# Team style\n", encoding="utf-8")
            (root / "AGENTS.md").write_text(
                '<!-- ew:route id="local-docs" triggers="documentation writing" '
                'owners="manuals/style.md#rules|skill://engineering-workflow/references/documentation_navigation.md" '
                'guards="manual_review:writing" -->\n',
                encoding="utf-8",
            )
            evidence = adoption.adoption_evidence(root, change_ids=[SEMANTIC_ID])
            self._record(root, evidence=evidence)
            before = adoption.assess_target_adoption(root, "0.10.0")
            self.assertIn("manuals/style.md", before["owner_snapshot"][SEMANTIC_ID])
            owner.write_text("# New team style\n", encoding="utf-8")
            self.assertIn(SEMANTIC_ID, adoption.assess_target_adoption(root, "0.10.0")["pending_change_ids"])

    def test_nested_agents_addition_change_and_deletion_invalidate_adoption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            self._record(root, evidence=adoption.adoption_evidence(root))
            (root / "manuals").mkdir()
            nested = root / "manuals/AGENTS.md"
            nested.write_text("# Scoped documentation instructions\n", encoding="utf-8")
            added = adoption.assess_target_adoption(root, "0.10.0")
            self.assertIn(SEMANTIC_ID, added["pending_change_ids"])
            self.assertIn("manuals/AGENTS.md", added["owner_snapshot"][SEMANTIC_ID])
            self._record(root, evidence=added["owner_evidence"])
            nested.write_text("# Changed scoped documentation instructions\n", encoding="utf-8")
            changed = adoption.assess_target_adoption(root, "0.10.0")
            self.assertIn(SEMANTIC_ID, changed["pending_change_ids"])
            self._record(root, evidence=changed["owner_evidence"])
            nested.unlink()
            self.assertIn(SEMANTIC_ID, adoption.assess_target_adoption(root, "0.10.0")["pending_change_ids"])

    def test_nested_documentation_route_owner_drift_invalidates_adoption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            (root / "manuals").mkdir()
            owner = root / "manuals/style.md"
            owner.write_text("# Local style rules\n", encoding="utf-8")
            (root / "manuals/AGENTS.md").write_text(
                '<!-- ew:route id="manual-writing" triggers="documentation writing" '
                'owners="manuals/style.md" guards="manual_review:local writing" -->\n',
                encoding="utf-8",
            )
            self._record(root, evidence=adoption.adoption_evidence(root))
            reviewed = adoption.assess_target_adoption(root, "0.10.0")
            self.assertIn("manuals/style.md", reviewed["owner_snapshot"][SEMANTIC_ID])
            self.assertIn(SEMANTIC_ID, reviewed["resolved_change_ids"])
            owner.write_text("# Changed local style rules\n", encoding="utf-8")
            self.assertIn(SEMANTIC_ID, adoption.assess_target_adoption(root, "0.10.0")["pending_change_ids"])

    def test_unreferenced_writing_owners_in_root_docs_and_custom_roots_are_discovered(self):
        for directory in ("docs", "manuals"):
            for filename in adoption.WRITING_OWNER_NAMES:
                with self.subTest(directory=directory, filename=filename), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    self._target(root)
                    (root / directory).mkdir(exist_ok=True)
                    relative = f"{directory}/{filename}"
                    owner = root / relative
                    owner.write_text("# Existing local writing owner\n", encoding="utf-8")
                    report = adoption.assess_target_adoption(root, "0.10.0")
                    for change in report["changes"]:
                        self.assertIn(relative, change["existing_owners"])
                        self.assertIn(relative, change["owner_snapshot"])
                    self._record(root, evidence=report["owner_evidence"])
                    owner.write_text("# Changed local writing owner\n", encoding="utf-8")
                    self.assertIn(SEMANTIC_ID, adoption.assess_target_adoption(root, "0.10.0")["pending_change_ids"])

    def test_plan_state_index_and_domain_changes_do_not_invalidate_owner_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            evidence = adoption.adoption_evidence(root)
            self._record(root, evidence=evidence)
            for relative in ("PLANS.md", "docs/README.md", "docs/engineering/architecture.md"):
                (root / relative).write_text("# Mutable content\n", encoding="utf-8")
            state = root / adoption.STATE_PATH
            state.write_text(state.read_text() + "active_plan: PLANS.md\n", encoding="utf-8")
            self.assertEqual(adoption.adoption_evidence(root), evidence)
            self.assertIn(SEMANTIC_ID, adoption.assess_target_adoption(root, "0.10.0")["resolved_change_ids"])

    def test_routed_readme_writing_prose_is_tracked_but_generated_index_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            (root / "AGENTS.md").write_text(
                '<!-- ew:route id="documentation" triggers="writing" owners="docs/README.md" '
                'guards="manual_review:writing owner" -->\n',
                encoding="utf-8",
            )
            owner = root / "docs/README.md"
            content = (
                "# Author writing rules\n\n"
                "<!-- engineering-workflow:index:start -->\n- old navigation\n"
                "<!-- engineering-workflow:index:end -->\n\nUse local vocabulary.\n"
            )
            owner.write_text(content, encoding="utf-8")
            evidence = adoption.adoption_evidence(root, change_ids=[SEMANTIC_ID])
            self._record(root, evidence=evidence)
            owner.write_text(content.replace("old navigation", "new navigation"), encoding="utf-8")
            self.assertEqual(adoption.adoption_evidence(root, change_ids=[SEMANTIC_ID]), evidence)
            owner.write_text(content.replace("local vocabulary", "different vocabulary"), encoding="utf-8")
            self.assertIn(SEMANTIC_ID, adoption.assess_target_adoption(root, "0.10.0")["pending_change_ids"])

    def test_owner_deletion_and_raw_byte_changes_invalidate_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            evidence = adoption.adoption_evidence(root, change_ids=[SEMANTIC_ID])
            self._record(root, evidence=evidence)
            owner = root / "docs/engineering/project_principles.md"
            owner.write_bytes(b"# Principles\r\n")
            self.assertNotEqual(adoption.adoption_evidence(root, change_ids=[SEMANTIC_ID]), evidence)
            owner.unlink()
            deleted = adoption.assess_target_adoption(root, "0.10.0")
            self.assertIn(SEMANTIC_ID, deleted["pending_change_ids"])
            self.assertIsNone(deleted["owner_snapshot"][SEMANTIC_ID]["docs/engineering/project_principles.md"])

    def test_symbolic_owner_leaf_parent_and_state_fail_closed(self):
        for location in ("leaf", "parent", "state"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "target"
                root.mkdir()
                self._target(root)
                outside = Path(tmp) / "outside"
                outside.mkdir()
                if location == "leaf":
                    (outside / "owner.md").write_text("private", encoding="utf-8")
                    (root / "AGENTS.md").unlink()
                    (root / "AGENTS.md").symlink_to(outside / "owner.md")
                elif location == "parent":
                    (root / "docs/engineering/project_principles.md").unlink()
                    (root / "docs/engineering").rmdir()
                    (root / "docs/engineering").symlink_to(outside, target_is_directory=True)
                else:
                    (outside / "state.yaml").write_text("private", encoding="utf-8")
                    (root / adoption.STATE_PATH).symlink_to(outside / "state.yaml")
                with self.assertRaises(ValueError):
                    adoption.assess_target_adoption(root, "0.10.0")

    def test_malformed_duplicate_and_unknown_evidence_is_rejected(self):
        invalid = [
            f"  {SEMANTIC_ID}: secret\n",
            f"  {SEMANTIC_ID}: {'a' * 64}\n  {SEMANTIC_ID}: {'b' * 64}\n",
            f"  unknown-id: {'a' * 64}\n",
            f"  {SEMANTIC_ID}: \"{'a' * 64}'\n",
            "adoption_evidence: {}\n",
        ]
        for entry in invalid:
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._target(root)
                self._record(root)
                state = root / adoption.STATE_PATH
                state.write_text(state.read_text() + "adoption_evidence:\n" + entry, encoding="utf-8")
                with self.assertRaises(ValueError):
                    adoption.assess_target_adoption(root, "0.10.0")

    def test_unknown_and_future_reviewed_ids_still_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            for identifier in (SEMANTIC_ID, "unknown-id"):
                with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                    adoption.assess_target_adoption(root, "0.9.10", [identifier])
            with self.assertRaises(ValueError):
                adoption.adoption_evidence(root, change_ids=["unknown-id"])

    def test_runtime_only_evidence_does_not_read_local_instruction_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").symlink_to("missing.md")
            self.assertEqual(adoption.adoption_evidence(root, change_ids=[RUNTIME_ID]), {})

    def test_partial_discovery_cannot_establish_recorded_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._target(root)
            self._record(root, evidence=adoption.adoption_evidence(root))
            partial = ([root / "AGENTS.md"], {"truncated": True, "omission_reasons": ["entry_limit"]})
            with patch.object(adoption, "discover_audit_files", return_value=partial):
                with self.assertRaisesRegex(ValueError, "Incomplete adoption owner discovery"):
                    adoption.adoption_evidence(root)
                with self.assertRaisesRegex(ValueError, "Incomplete adoption owner discovery"):
                    adoption.assess_target_adoption(root, "0.10.0")

    def test_public_state_parser_accepts_optional_and_valid_evidence(self):
        digest = "a" * 64
        self.assertEqual(adoption.recorded_adoption_evidence("skill_version: 0.10.0\n"), {})
        self.assertEqual(adoption.recorded_adoption_evidence("adoption_evidence: {}\n"), {})
        self.assertEqual(
            adoption.recorded_adoption_evidence(f"adoption_evidence:\n  {SEMANTIC_ID}: '{digest}'\nnext: value\n"),
            {SEMANTIC_ID: digest},
        )
        with self.assertRaises(ValueError):
            adoption.recorded_adoption_evidence(f"adoption_evidence: {{}}\n  {SEMANTIC_ID}: {digest}\n")


if __name__ == "__main__":
    unittest.main()
