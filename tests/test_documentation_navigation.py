from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module

navigation = load_script_module("documentation_navigation")


def write(root: Path, relative: str, text: str = "# Heading\n") -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def index(body: str = "", *, before: str = "# Local navigation\n\n", after: str = "\nLocal prose.\n") -> str:
    return f"{before}{navigation.INDEX_MARKER_START}\n{body}\n{navigation.INDEX_MARKER_END}{after}"


def state(root: Path, *, roots=(), indexes=(), managed=()) -> None:
    lines = ["schema_version: 2"]
    for key, values in (("documentation_roots", roots), ("documentation_indexes", indexes), ("managed_paths", managed)):
        if values:
            lines.extend([f"{key}:", *(f"  - {value}" for value in values)])
    write(root, navigation.STATE_MANIFEST_PATH, "\n".join(lines) + "\n")


class DocumentationNavigationTests(unittest.TestCase):
    def test_map_reads_only_route_metadata_and_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "README.md", "Sensitive body must not enter a map.")
            write(root, "docs/domain.md", "Unique body must not enter a map.")
            write(root, "rules/policy.md", "# Owner\n")
            write(
                root,
                "AGENTS.md",
                '<!-- ew:route id="domain" triggers="src/**" owners="rules/policy.md|skill://engineering-workflow/reference" guards="manual_review:policy" -->\n',
            )
            original = Path.open
            inspected = []

            def guard(path, *args, **kwargs):
                inspected.append(path.relative_to(root.resolve()).as_posix())
                self.assertEqual(path.name, "AGENTS.md")
                return original(path, *args, **kwargs)

            with (
                mock.patch.object(Path, "open", guard),
                mock.patch.object(Path, "read_bytes", side_effect=AssertionError("Body read")),
            ):
                result = navigation.build_documentation_map(root)
            self.assertEqual(inspected, ["AGENTS.md"])
            paths = {item["path"]: item for item in result["nodes"]}
            self.assertIn("README.md", paths)
            self.assertEqual(paths["rules/policy.md"]["routes"], ["domain"])
            self.assertEqual(paths["rules/policy.md"]["ownership"], "protected")
            self.assertIn("skill://engineering-workflow/reference", paths)
            self.assertNotIn("Unique body", json.dumps(result))

    def test_manifest_roots_are_scope_without_ownership(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state(root, roots=["handbook"])
            write(root, "handbook/domain.md")
            write(root, "docs/outside.md")
            report = navigation.build_documentation_map(root)
            paths = {item["path"] for item in report["nodes"]}
            self.assertIn("handbook/domain.md", paths)
            self.assertNotIn("docs/outside.md", paths)
            self.assertEqual(navigation.planned_documentation_index_writes(root), {})
            self.assertEqual(report["discovery"]["scope_excluded_document_count"], 1)

    def test_explicit_source_reference_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/overview.md")
            write(root, "skill/engineering-workflow/references/owner.md")
            report = navigation.build_documentation_map(root, roots=["docs", "skill/engineering-workflow/references"])
            self.assertIn("skill/engineering-workflow/references/owner.md", {item["path"] for item in report["nodes"]})

    def test_git_discovery_ignored_and_odd_names_are_honest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            write(root, ".gitignore", "ignored/\n")
            write(root, "docs/odd name α.md")
            write(root, "ignored/private.md")
            report = navigation.build_documentation_map(root, roots=["."])
            self.assertEqual(report["discovery"]["mode"], "git")
            self.assertIn("docs/odd name α.md", {item["path"] for item in report["nodes"]})
            self.assertNotIn("ignored/private.md", {item["path"] for item in report["nodes"]})

    @unittest.skipIf(os.name == "nt", "POSIX permits these filesystem names")
    def test_control_and_non_utf8_names_are_complete_but_safely_displayed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            odd = ["docs/name\nline.md", os.fsdecode(b"docs/nonutf8-\xff.md")]
            write(root, odd[0])
            # macOS filesystems reject undecodable bytes; a supplied Git-style
            # inventory must still represent and safely display that path.
            report = navigation.build_documentation_map(root, inventory=[root / path for path in odd])
            self.assertTrue(set(odd) <= {node["path"] for node in report["nodes"]})
            tree = navigation.render_documentation_tree(report)
            self.assertIn("name\\nline.md", tree)
            self.assertIn("nonutf8-\\udcff.md", tree)
            self.assertLessEqual(len(tree.encode()), 8192)
            write(root, "docs/README.md", index())
            with self.assertRaises(navigation.NavigationError):
                navigation.planned_documentation_index_writes(root)

    def test_symbolic_paths_never_followed(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as outside:
            root = Path(temporary)
            write(Path(outside), "secret.md")
            (root / "docs").mkdir()
            (root / "docs/symbolic.md").symlink_to(Path(outside) / "secret.md")
            (root / "linked").symlink_to(outside, target_is_directory=True)
            report = navigation.build_documentation_map(root)
            node = next(n for n in report["nodes"] if n["path"] == "docs/symbolic.md")
            self.assertEqual(node["status"], "unsafe")
            with self.assertRaises(navigation.NavigationError):
                navigation.build_documentation_map(root, ["linked"])
            with self.assertRaises(navigation.NavigationError):
                navigation.build_documentation_map(root, ["../outside"])

    def test_map_determinism_inventory_reuse_and_partial_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            a = write(root, "docs/a.md")
            b = write(root, "docs/b.md")
            metadata = {"mode": "bounded_filesystem", "truncated": True, "omission_reasons": ["entry_limit"]}
            with mock.patch.object(
                navigation, "discover_audit_files", side_effect=AssertionError("Inventory rediscovered")
            ):
                first = navigation.build_documentation_map(root, inventory=([b, a], metadata))
                second = navigation.build_documentation_map(root, inventory=([a, b], metadata))
            self.assertEqual(first, second)
            self.assertTrue(first["discovery"]["truncated"])
            self.assertIn("discovery_incomplete", {w["code"] for w in first["warnings"]})
            self.assertNotIn("rejected_path_count", metadata)

    def test_tree_budget_and_focused_collapsed_expansion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for i in range(130):
                write(root, f"docs/huge/α-{i:03d}.md")
            for name in ("archive", "generated", "vendor"):
                write(root, f"docs/{name}/hidden.md")
            # Provided inventory proves tracked vendor content can be represented,
            # unlike the intentionally pruned non-Git fallback.
            inventory = [p for p in root.rglob("*.md")]
            report = navigation.build_documentation_map(root, inventory=inventory)
            tree = navigation.render_documentation_tree(report)
            self.assertLessEqual(len(tree.encode("utf-8")), 8192)
            self.assertLessEqual(len(tree.splitlines()) - 3, 120)
            self.assertIn("archive/ (1 documents, collapsed)", tree)
            expanded = navigation.render_documentation_tree(report, "docs/archive")
            self.assertIn("hidden.md", expanded)
            self.assertNotIn("α-", expanded)
            self.assertEqual(report, navigation.build_documentation_map(root, inventory=list(reversed(inventory))))

    def test_proposals_preserve_prose_descriptions_and_language(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before, after = "# Навигация\r\n\r\n", "\n\nОригинальный текст.\n"
            existing = index("- [Описание](domain.md) — пояснение", before=before, after=after)
            target = write(root, "docs/README.md", existing)
            write(root, "docs/domain.md")
            write(root, "docs/new name α.md")
            proposed = navigation.planned_documentation_index_writes(root)
            self.assertIn("new%20name%20%CE%B1.md", proposed["docs/README.md"].decode())
            self.assertIn("- [Описание](domain.md) — пояснение", proposed["docs/README.md"].decode())
            self.assertEqual(target.read_bytes(), existing.encode())
            # read_text normalizes CRLF, so exact outside-marker bytes matter.
            self.assertTrue(proposed["docs/README.md"].startswith(before.encode()))
            self.assertTrue(proposed["docs/README.md"].endswith(after.encode()))
            target.write_bytes(proposed["docs/README.md"])
            self.assertEqual(navigation.planned_documentation_index_writes(root), proposed)
            self.assertTrue(navigation.check_documentation(root)["success"])

    def test_unmarked_readmes_are_never_owned_by_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = write(root, "docs/README.md", "# Authored\nNarrative.\n")
            write(root, "docs/domain.md")
            self.assertEqual(navigation.planned_documentation_index_writes(root), {})
            self.assertTrue(navigation.check_documentation(root)["success"])
            state(root, indexes=["docs/README.md"], managed=["docs/README.md"])
            with self.assertRaises(navigation.NavigationError) as error:
                navigation.planned_documentation_index_writes(root)
            self.assertEqual(error.exception.code, "index_unmanaged")
            self.assertEqual(target.read_text(), "# Authored\nNarrative.\n")

    def test_missing_index_requires_exact_manifest_ownership(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state(root, roots=["handbook"], indexes=["handbook/navigation.md"])
            write(root, "handbook/doc.md")
            with self.assertRaises(navigation.NavigationError) as error:
                navigation.planned_documentation_index_writes(root)
            self.assertEqual(error.exception.code, "index_ownership_missing")
            state(root, roots=["handbook"], indexes=["handbook/navigation.md"], managed=["handbook/navigation.md"])
            writes = navigation.planned_documentation_index_writes(root, extra_files=["handbook/future.md"])
            self.assertEqual(set(writes), {"handbook/navigation.md"})
            self.assertIn("future.md", writes["handbook/navigation.md"].decode())
            self.assertFalse((root / "handbook/navigation.md").exists())

    def test_index_graph_uses_child_indexes_without_duplicate_descendants(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/README.md", index())
            write(root, "docs/child/README.md", index())
            write(root, "docs/child/deep.md")
            writes = navigation.planned_documentation_index_writes(root)
            self.assertIn("child/README.md", writes["docs/README.md"].decode())
            self.assertNotIn("deep.md", writes["docs/README.md"].decode())
            self.assertIn("deep.md", writes["docs/child/README.md"].decode())

    def test_custom_archive_graph_successors_survive_generic_planning(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            graph = ["docs/product/plans/archive/README.md", "docs/product/PLANS_ARCHIVE.md", "docs/README.md"]
            state(root, managed=graph)
            manifest = root / navigation.STATE_MANIFEST_PATH
            manifest.write_text(
                manifest.read_text()
                + "active_plan: null\nplan_archive_path: docs/product/plans/archive\nplan_archive_indexes:\n"
                + "".join(f"  - {p}\n" for p in graph)
            )
            write(root, graph[0], index("- [Historical record](old.md) — retained evidence"))
            write(root, graph[1], index("- [Plan records](plans/archive/README.md) — category"))
            write(root, graph[2], index("- [History](product/PLANS_ARCHIVE.md) — rationale"))
            write(root, "docs/product/plans/archive/old.md")
            write(root, "docs/current.md")
            write(root, "docs/product/domain.md")
            proposals = navigation.planned_documentation_index_writes(root)
            parent = proposals[graph[2]].decode()
            self.assertIn("[History](product/PLANS_ARCHIVE.md) — rationale", parent)
            self.assertIn("current.md", parent)
            self.assertIn("product/domain.md", parent)
            self.assertNotIn("plans/archive/README.md", parent)
            self.assertNotIn("old.md", parent)
            self.assertIn("[Plan records](plans/archive/README.md) — category", proposals[graph[1]].decode())
            for path, payload in proposals.items():
                (root / path).write_bytes(payload)
            self.assertTrue(navigation.check_documentation(root)["success"])
            lifecycle = load_script_module("plan_lifecycle")
            layout = lifecycle.resolve_archive_layout(root.resolve())
            archive_check = lifecycle.check_explicit_archive_graph(root.resolve(), layout)
            self.assertTrue(archive_check["success"], archive_check)

    def test_declared_lazy_archive_graph_does_not_create_empty_archive_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            graph = ["docs/archive/plans/README.md", "docs/archive/README.md", "docs/README.md"]
            state(root, roots=["docs"], managed=graph)
            manifest = root / navigation.STATE_MANIFEST_PATH
            manifest.write_text(
                manifest.read_text()
                + "active_plan: PLANS.md\nplan_archive_path: docs/archive/plans\nplan_archive_indexes:\n"
                + "".join(f"  - {p}\n" for p in graph)
            )
            write(root, "docs/README.md", index())
            write(root, "docs/active.md")
            self.assertNotIn("docs/archive/README.md", navigation.documentation_index_targets(root, "docs/README.md"))
            proposals = navigation.planned_documentation_index_writes(root)
            self.assertEqual(set(proposals), {"docs/README.md"})
            self.assertNotIn("archive/README.md", proposals["docs/README.md"].decode())
            self.assertFalse((root / "docs/archive").exists())

    def test_index_staleness_warns_until_explicit_document_root_adoption(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/README.md", index())
            write(root, "docs/domain.md")
            result = navigation.check_documentation(root)
            self.assertTrue(result["success"])
            self.assertIn("index_stale", {w["code"] for w in result["warnings"]})
            state(root, roots=["docs"])
            adopted = navigation.check_documentation(root)
            self.assertFalse(adopted["success"])
            self.assertIn("index_stale", {e["code"] for e in adopted["errors"]})

    def test_preexisting_link_defects_warn_changed_and_managed_defects_block(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/old.md", "[missing](absent.md)\n[escape](../../absent.md)\n")
            result = navigation.check_documentation(root)
            self.assertTrue(result["success"], result)
            self.assertEqual({w["code"] for w in result["warnings"]}, {"link_missing", "link_escape"})
            changed = navigation.check_documentation(root, changed_paths=["docs/old.md"])
            self.assertFalse(changed["success"])
            self.assertEqual({e["code"] for e in changed["errors"]}, {"link_missing", "link_escape"})
            write(root, "docs/README.md", index("- [missing](absent.md)"))
            managed = navigation.check_documentation(root)
            self.assertIn("link_missing", {e["code"] for e in managed["errors"]})

    def test_anchors_references_titles_fences_and_external_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/target (α).md", '# Заголовок\n# Repeat\n# Repeat\n<h2 id="explicit">Title</h2>\n')
            valid = '[unicode](<target (α).md#заголовок>)\n[duplicate](target%20%28%CE%B1%29.md#repeat-1 "Title")\n[ref][owner]\n[owner]: <target (α).md#explicit>\n[external](https://example.invalid/path#anything)\n```md\n[example](absent.md)\n```\n`[inline](absent.md)`\n'
            write(root, "docs/source.md", valid)
            self.assertTrue(navigation.check_documentation(root, changed_paths=["docs/source.md"])["success"])
            write(root, "docs/source.md", valid + "[bad](target%20%28%CE%B1%29.md#missing)\n")
            result = navigation.check_documentation(root, changed_paths=["docs/source.md"])
            self.assertEqual([e["code"] for e in result["errors"]], ["anchor_missing"])

    def test_unsupported_syntax_warns_without_false_completeness(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/source.md", "[undefined][unknown]\n[query](target.md?view=raw)\n")
            result = navigation.check_documentation(root, changed_paths=["docs/source.md"])
            self.assertTrue(result["success"])
            self.assertEqual([w["code"] for w in result["warnings"]], ["link_unsupported", "link_unsupported"])
            self.assertIn("parser", result)

    def test_changed_document_outside_default_roots_is_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "handbook/change.md", "[missing](absent.md)\n")
            result = navigation.check_documentation(root, changed_paths=["handbook/change.md"])
            self.assertFalse(result["success"])
            self.assertEqual(result["errors"][0]["code"], "link_missing")
            self.assertIn("handbook/change.md", result["checked_paths"])

    def test_route_owner_anchors_block_changed_or_managed_routers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/owner.md", "# Existing heading\n")
            write(
                root,
                "AGENTS.md",
                '<!-- ew:route id="policy" triggers="src/**" owners="docs/owner.md#missing" guards="manual_review:policy" -->\n',
            )
            preexisting = navigation.check_documentation(root)
            self.assertTrue(preexisting["success"], preexisting)
            self.assertIn("route_owner_anchor_missing", {w["code"] for w in preexisting["warnings"]})
            changed = navigation.check_documentation(root, changed_paths=["AGENTS.md"])
            self.assertFalse(changed["success"])
            self.assertIn("route_owner_anchor_missing", {e["code"] for e in changed["errors"]})
            state(root, managed=["AGENTS.md"])
            managed = navigation.check_documentation(root)
            self.assertFalse(managed["success"])
            self.assertIn("route_owner_anchor_missing", {e["code"] for e in managed["errors"]})
            write(
                root,
                "AGENTS.md",
                '<!-- ew:route id="policy" triggers="src/**" owners="docs/owner.md#existing-heading" guards="manual_review:policy" -->\n',
            )
            self.assertTrue(navigation.check_documentation(root)["success"])

    def test_nested_router_owners_resolve_from_repository_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/owner.md", "# Heading\n")
            write(
                root,
                "src/AGENTS.md",
                '<!-- ew:route id="policy" triggers="src/**" owners="docs/owner.md#heading" guards="manual_review:policy" -->\n',
            )
            self.assertTrue(navigation.check_documentation(root, changed_paths=["src/AGENTS.md"])["success"])
            write(
                root,
                "src/AGENTS.md",
                '<!-- ew:route id="policy" triggers="src/**" owners="docs/missing.md" guards="manual_review:policy" -->\n',
            )
            result = navigation.check_documentation(root, changed_paths=["src/AGENTS.md"])
            self.assertFalse(result["success"])
            self.assertIn("route_owner_missing", {e["code"] for e in result["errors"]})

    def test_declared_custom_archive_is_historical_and_collapsed_only_at_exact_branch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            graph = ["manuals/history/README.md", "manuals/README.md"]
            state(root, managed=graph)
            manifest = root / navigation.STATE_MANIFEST_PATH
            manifest.write_text(
                manifest.read_text()
                + "active_plan: PLANS.md\nplan_archive_path: manuals/history\nplan_archive_indexes:\n"
                + "".join(f"  - {p}\n" for p in graph)
            )
            write(root, graph[0], index())
            write(root, graph[1], index())
            write(root, "manuals/history/old.md")
            write(root, "manuals/history-other/current.md")
            report = navigation.build_documentation_map(root, roots=["manuals"])
            nodes = {n["path"]: n for n in report["nodes"]}
            self.assertTrue(nodes["manuals/history"]["collapse_by_default"])
            self.assertEqual(nodes["manuals/history/old.md"]["ownership"], "historical")
            self.assertEqual(nodes["manuals/history-other/current.md"]["ownership"], "unknown")
            self.assertFalse(nodes["manuals/history-other"]["collapse_by_default"])
            self.assertTrue(nodes[graph[0]]["archive_index"])
            tree = navigation.render_documentation_tree(report)
            self.assertIn("history/ (2 documents, collapsed)", tree)
            self.assertNotIn("old.md", tree)
            self.assertIn("old.md", navigation.render_documentation_tree(report, "manuals/history"))
            implicit = navigation.build_documentation_map(root)
            self.assertIn("manuals/history/old.md", {n["path"] for n in implicit["nodes"]})

    def test_source_map_and_check_never_load_maintainer_or_fixture_agents(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "skill/engineering-workflow/SKILL.md")
            self.assertFalse(navigation.recognized_source_repository(root))
            write(root, "scripts/build_marketplace_package.py", "# Not executed.\n")
            self.assertTrue(navigation.recognized_source_repository(root))
            write(
                root,
                "AGENTS.md",
                '<!-- ew:route id="maintainer" triggers="**" owners="missing-root.md" guards="manual_review:policy" -->\n',
            )
            write(
                root,
                "tests/fixtures/example/AGENTS.md",
                '<!-- ew:route id="fixture" triggers="**" owners="missing-fixture.md" guards="manual_review:policy" -->\n',
            )
            write(root, "README.md", "[Source policy](AGENTS.md#routing)\n")
            write(root, "skill/engineering-workflow/references/owner.md")
            original = navigation._text

            def guard(repository, relative):
                self.assertNotEqual(Path(relative).name, "AGENTS.md")
                return original(repository, relative)

            with mock.patch.object(navigation, "_text", side_effect=guard):
                report = navigation.build_documentation_map(root)
                checked = navigation.check_documentation(root, roots=["."])
            self.assertEqual(report["routes"], [])
            self.assertTrue(report["source_maintainer_routes_not_loaded"])
            nodes = {n["path"]: n for n in report["nodes"]}
            self.assertIn("skill/engineering-workflow/references/owner.md", nodes)
            self.assertFalse(nodes["AGENTS.md"]["policy_metadata_loaded"])
            self.assertFalse(nodes["tests/fixtures/example/AGENTS.md"]["policy_metadata_loaded"])
            self.assertNotIn("missing-fixture.md", nodes)
            self.assertNotIn("missing-root.md", nodes)
            self.assertTrue(checked["success"], checked)
            self.assertTrue(checked["source_maintainer_routes_not_loaded"])
            self.assertNotIn("AGENTS.md", checked["checked_paths"])
            self.assertNotIn("tests/fixtures/example/AGENTS.md", checked["checked_paths"])

    def test_map_and_check_entrypoints_create_no_bytecode_when_environment_is_unset(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scripts = root / "trusted-scripts"
            scripts.mkdir()
            source_scripts = Path(navigation.__file__).parent
            for name in ("documentation_navigation.py", "common.py"):
                shutil.copyfile(source_scripts / name, scripts / name)
            target = root / "target"
            write(target, "docs/owner.md")
            environment = dict(os.environ)
            for key in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX", "PYTHONPATH"):
                environment.pop(key, None)
            for command in ("map", "check"):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(scripts / "documentation_navigation.py"),
                        command,
                        "--repo-root",
                        str(target),
                        "--format",
                        "json",
                    ],
                    cwd=target,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                json.loads(completed.stdout)
            self.assertFalse(list(root.rglob("__pycache__")))
            self.assertFalse(list(root.rglob("*.pyc")))

    def test_partial_inventory_cannot_remove_unseen_index_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = write(root, "docs/README.md", index("- [Unseen](unseen.md)"))
            metadata = {"mode": "bounded_filesystem", "truncated": True, "omission_reasons": ["entry_limit"]}
            with mock.patch.object(navigation, "discover_audit_files", return_value=([target], metadata)):
                with self.assertRaises(navigation.NavigationError) as error:
                    navigation.planned_documentation_index_writes(root)
                self.assertEqual(error.exception.code, "discovery_incomplete")

    def test_malformed_managed_markers_and_manifest_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/README.md", navigation.INDEX_MARKER_START + "\nNo end\n")
            result = navigation.check_documentation(root)
            self.assertEqual(result["errors"][0]["code"], "index_markers_invalid")
            write(root, navigation.STATE_MANIFEST_PATH, "documentation_roots:\n  - ../escape\n")
            with self.assertRaises(navigation.NavigationError) as error:
                navigation.build_documentation_map(root)
            self.assertEqual(error.exception.code, "documentation_config_invalid")

    def test_marker_examples_in_prose_or_code_do_not_claim_ownership(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            body = (
                f"An index uses `{navigation.INDEX_MARKER_START}` and `{navigation.INDEX_MARKER_END}`.\r\n"
                f"```markdown\r\n{navigation.INDEX_MARKER_START}\r\n"
                f"- [Example](missing.md)\r\n{navigation.INDEX_MARKER_END}\r\n```\r\n"
            )
            target = write(root, "references/contract.md", body)
            self.assertEqual(navigation.planned_documentation_index_writes(root, ["references"]), {})
            self.assertEqual(target.read_bytes(), body.encode())

    def test_generated_links_support_brackets_and_parentheses_in_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/README.md", index())
            write(root, "docs/odd [α] (name).md")
            proposals = navigation.planned_documentation_index_writes(root)
            (root / "docs/README.md").write_bytes(proposals["docs/README.md"])
            result = navigation.check_documentation(root)
            self.assertTrue(result["success"], result)
            self.assertEqual(result["warnings"], [])

    def test_example_routes_do_not_add_false_local_owners(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(
                root,
                "AGENTS.md",
                '```md\n<!-- ew:route id="example" triggers="src/**" owners="absent.md" guards="manual_review:example" -->\n```\n',
            )
            report = navigation.build_documentation_map(root)
            self.assertEqual(report["routes"], [])
            self.assertNotIn("absent.md", {n["path"] for n in report["nodes"]})

    def test_managed_offsets_after_crlf_fence_preserve_exact_prose(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before = "# Local\r\n```markdown\r\nAn example.\r\n```\r\n\r\n"
            write(root, "docs/README.md", index(before=before))
            write(root, "docs/domain.md")
            proposals = navigation.planned_documentation_index_writes(root)
            self.assertTrue(proposals["docs/README.md"].startswith(before.encode()))
            (root / "docs/README.md").write_bytes(proposals["docs/README.md"])
            self.assertEqual(navigation.planned_documentation_index_writes(root), proposals)

    def test_full_report_is_private_outside_repository_and_cli_is_read_only(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as protected:
            root = Path(temporary)
            write(root, "docs/domain.md")
            destination = Path(protected) / "report.json"
            before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = navigation.main(["map", "--repo-root", str(root), "--full-report", str(destination)])
            self.assertEqual(code, 0)
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
            self.assertEqual(json.loads(destination.read_text())["schema_version"], 1)
            self.assertEqual(before, sorted(p.relative_to(root).as_posix() for p in root.rglob("*")))
            with self.assertRaises(navigation.NavigationError):
                navigation._write_full_report(root, root / "report.json", {})
            destination.unlink()
            destination.symlink_to(root / "outside.json")
            with self.assertRaises(navigation.NavigationError):
                navigation._write_full_report(root, destination, {})

    def test_cli_json_is_one_complete_document(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as protected:
            root = Path(temporary)
            write(root, "docs/domain.md")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                navigation.main(
                    [
                        "map",
                        "--repo-root",
                        str(root),
                        "--format",
                        "json",
                        "--full-report",
                        str(Path(protected) / "report.json"),
                    ]
                )
            self.assertEqual(json.loads(output.getvalue())["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
