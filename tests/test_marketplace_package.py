from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO_ROOT / "scripts" / "build_marketplace_package.py"
SPEC = importlib.util.spec_from_file_location("build_marketplace_package", BUILDER_PATH)
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)


class MarketplacePackageTests(unittest.TestCase):
    def test_repository_package_matches_deterministic_builder(self):
        completed = subprocess.run(
            [sys.executable, str(BUILDER_PATH), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(result["success"], result)
        self.assertEqual(result["version"], "0.8.1")
        self.assertEqual(result["drift"], [])

    def test_check_detects_packaged_skill_byte_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin_root = root / "plugins" / "engineering-workflow"
            plugin_root.parent.mkdir(parents=True)
            codex_catalog = root / ".agents/plugins/marketplace.json"
            claude_catalog = root / ".claude-plugin/marketplace.json"
            with mock.patch.multiple(
                builder,
                REPO_ROOT=root,
                SOURCE_SKILL=REPO_ROOT / "skill/engineering-workflow",
                PLUGIN_ROOT=plugin_root,
                PACKAGED_SKILL=plugin_root / "skills/engineering-workflow",
                CODEX_MARKETPLACE=codex_catalog,
                CLAUDE_MARKETPLACE=claude_catalog,
            ):
                expected = root / "expected"
                builder._build_expected(expected, "0.8.1")
                builder.write_package(expected)
                comparison = root / "comparison"
                builder._build_expected(comparison, "0.8.1")
                self.assertEqual(builder._drift(comparison), [])
                skill = plugin_root / "skills/engineering-workflow/SKILL.md"
                skill.write_bytes(skill.read_bytes() + b"\n")
                self.assertIn("changed:skills/engineering-workflow/SKILL.md", builder._drift(comparison))

    def test_catalog_failure_restores_previous_package_and_catalogs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin_root = root / "plugins" / "engineering-workflow"
            plugin_root.parent.mkdir(parents=True)
            codex_catalog = root / ".agents/plugins/marketplace.json"
            claude_catalog = root / ".claude-plugin/marketplace.json"
            with mock.patch.multiple(
                builder,
                REPO_ROOT=root,
                SOURCE_SKILL=REPO_ROOT / "skill/engineering-workflow",
                PLUGIN_ROOT=plugin_root,
                PACKAGED_SKILL=plugin_root / "skills/engineering-workflow",
                CODEX_MARKETPLACE=codex_catalog,
                CLAUDE_MARKETPLACE=claude_catalog,
            ):
                initial = root / "initial"
                builder._build_expected(initial, "0.8.1")
                builder.write_package(initial)
                before_tree = builder._tree_state(plugin_root)
                before_catalogs = (codex_catalog.read_bytes(), claude_catalog.read_bytes())
                replacement = root / "replacement"
                builder._build_expected(replacement, "0.8.1")
                original_write = builder._atomic_write
                failed = False

                def fail_claude_catalog(path, data):
                    nonlocal failed
                    if path == claude_catalog and not failed:
                        failed = True
                        raise OSError("synthetic catalog failure")
                    original_write(path, data)

                with mock.patch.object(builder, "_atomic_write", side_effect=fail_claude_catalog):
                    with self.assertRaises(OSError):
                        builder.write_package(replacement)

                self.assertEqual(builder._tree_state(plugin_root), before_tree)
                self.assertEqual(
                    (codex_catalog.read_bytes(), claude_catalog.read_bytes()),
                    before_catalogs,
                )
                self.assertFalse((plugin_root.parent / ".engineering-workflow.previous").exists())

    def test_manifests_declare_only_self_contained_skill_capability(self):
        codex = json.loads(
            (REPO_ROOT / "plugins/engineering-workflow/.codex-plugin/plugin.json").read_text(
                encoding="utf-8"
            )
        )
        claude = json.loads(
            (REPO_ROOT / "plugins/engineering-workflow/.claude-plugin/plugin.json").read_text(
                encoding="utf-8"
            )
        )
        for manifest in (codex, claude):
            self.assertEqual(manifest["version"], "0.8.1")
            self.assertEqual(manifest["repository"], builder.REPOSITORY_URL)
            self.assertNotIn("mcpServers", manifest)
            self.assertNotIn("apps", manifest)
            self.assertNotIn("hooks", manifest)
        self.assertEqual(codex["skills"], "./skills/")
        self.assertEqual(codex["interface"]["category"], "Developer Tools")
        self.assertNotIn("category", claude)


if __name__ == "__main__":
    unittest.main()
