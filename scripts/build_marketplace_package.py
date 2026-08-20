#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILL = REPO_ROOT / "skill" / "engineering-workflow"
PLUGIN_ROOT = REPO_ROOT / "plugins" / "engineering-workflow"
PACKAGED_SKILL = PLUGIN_ROOT / "skills" / "engineering-workflow"
CODEX_MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
CLAUDE_MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN_NAME = "engineering-workflow"
MARKETPLACE_NAME = "xeonvs-engineering"
REPOSITORY_URL = "https://github.com/xeonvs/codex-engineering-workflow"
IGNORED_NAMES = {"__pycache__", ".DS_Store"}


class PackageError(RuntimeError):
    pass


def _skill_version() -> str:
    text = (SOURCE_SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s*version:\s*([0-9A-Za-z.+-]+)\s*$", text)
    if not match:
        raise PackageError("canonical SKILL.md has no metadata.version")
    return match.group(1)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _codex_manifest(version: str) -> dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "version": version,
        "description": "Audit, plan, migrate, validate, and maintain repository engineering workflows.",
        "author": {
            "name": "xeonvs",
            "url": "https://github.com/xeonvs",
        },
        "homepage": REPOSITORY_URL,
        "repository": REPOSITORY_URL,
        "license": "MIT",
        "keywords": ["engineering", "workflow", "repository", "planning", "validation"],
        "skills": "./skills/",
        "interface": {
            "displayName": "Engineering Workflow",
            "shortDescription": "Plan and maintain repository workflows safely.",
            "longDescription": "Audits, scaffolds, validates, updates, and conservatively migrates repository engineering-workflow layers.",
            "developerName": "xeonvs",
            "category": "Developer Tools",
            "capabilities": ["Interactive", "Read", "Write"],
            "websiteURL": REPOSITORY_URL,
            "defaultPrompt": [
                "Audit this repository's engineering workflow.",
                "Upgrade this repository's workflow safely.",
            ],
        },
    }


def _claude_manifest(version: str) -> dict[str, Any]:
    return {
        "name": PLUGIN_NAME,
        "version": version,
        "description": "Audit, plan, migrate, validate, and maintain repository engineering workflows.",
        "author": {
            "name": "xeonvs",
            "url": "https://github.com/xeonvs",
        },
        "homepage": REPOSITORY_URL,
        "repository": REPOSITORY_URL,
        "license": "MIT",
        "keywords": ["engineering", "workflow", "repository", "planning", "validation"],
    }


def _codex_catalog() -> dict[str, Any]:
    return {
        "name": MARKETPLACE_NAME,
        "interface": {"displayName": "Xeonvs Engineering"},
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "source": {"source": "local", "path": "./plugins/engineering-workflow"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }
        ],
    }


def _claude_catalog() -> dict[str, Any]:
    return {
        "name": MARKETPLACE_NAME,
        "owner": {"name": "xeonvs"},
        "description": "Public engineering workflow plugins maintained by xeonvs.",
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "source": "./plugins/engineering-workflow",
                "description": "Audit, plan, migrate, validate, and maintain repository engineering workflows.",
                "category": "Developer Tools",
                "homepage": REPOSITORY_URL,
            }
        ],
    }


def _iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in SOURCE_SKILL.rglob("*"):
        relative = path.relative_to(SOURCE_SKILL)
        if any(part in IGNORED_NAMES for part in relative.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise PackageError(f"canonical skill contains unsupported symlink: {relative.as_posix()}")
        if path.is_file():
            files.append(relative)
    return sorted(files, key=lambda item: item.as_posix())


def _copy_skill(destination: Path) -> None:
    destination.mkdir(parents=True)
    for relative in _iter_source_files():
        source = SOURCE_SKILL / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _build_expected(destination: Path, version: str) -> None:
    (destination / ".codex-plugin").mkdir(parents=True)
    (destination / ".claude-plugin").mkdir(parents=True)
    (destination / ".codex-plugin" / "plugin.json").write_bytes(
        _json_bytes(_codex_manifest(version))
    )
    (destination / ".claude-plugin" / "plugin.json").write_bytes(
        _json_bytes(_claude_manifest(version))
    )
    _copy_skill(destination / "skills" / PLUGIN_NAME)


def _tree_state(root: Path) -> dict[str, tuple[bytes, bool]]:
    if not root.is_dir():
        return {}
    state: dict[str, tuple[bytes, bool]] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise PackageError(f"generated package contains a symlink: {path.relative_to(root)}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            executable = bool(path.stat().st_mode & stat.S_IXUSR)
            state[relative] = (path.read_bytes(), executable)
    return state


def _drift(expected: Path) -> list[str]:
    expected_state = _tree_state(expected)
    actual_state = _tree_state(PLUGIN_ROOT)
    drift: list[str] = []
    for relative in sorted(expected_state.keys() - actual_state.keys()):
        drift.append(f"missing:{relative}")
    for relative in sorted(actual_state.keys() - expected_state.keys()):
        drift.append(f"unexpected:{relative}")
    for relative in sorted(expected_state.keys() & actual_state.keys()):
        if expected_state[relative] != actual_state[relative]:
            drift.append(f"changed:{relative}")
    expected_catalogs = {
        CODEX_MARKETPLACE: _json_bytes(_codex_catalog()),
        CLAUDE_MARKETPLACE: _json_bytes(_claude_catalog()),
    }
    for path, expected_bytes in expected_catalogs.items():
        if not path.is_file():
            drift.append(f"missing:{path.relative_to(REPO_ROOT).as_posix()}")
        elif path.read_bytes() != expected_bytes:
            drift.append(f"changed:{path.relative_to(REPO_ROOT).as_posix()}")
    return drift


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_package(expected: Path) -> None:
    PLUGIN_ROOT.parent.mkdir(parents=True, exist_ok=True)
    if PLUGIN_ROOT.is_symlink() or CODEX_MARKETPLACE.is_symlink() or CLAUDE_MARKETPLACE.is_symlink():
        raise PackageError("marketplace outputs must not be symbolic links")
    backup = PLUGIN_ROOT.parent / f".{PLUGIN_NAME}.previous"
    catalog_snapshots = {
        path: path.read_bytes() if path.is_file() else None
        for path in (CODEX_MARKETPLACE, CLAUDE_MARKETPLACE)
    }
    if backup.exists():
        shutil.rmtree(backup)
    if PLUGIN_ROOT.exists():
        os.replace(PLUGIN_ROOT, backup)
    try:
        os.replace(expected, PLUGIN_ROOT)
        _atomic_write(CODEX_MARKETPLACE, _json_bytes(_codex_catalog()))
        _atomic_write(CLAUDE_MARKETPLACE, _json_bytes(_claude_catalog()))
    except Exception:
        if PLUGIN_ROOT.exists():
            shutil.rmtree(PLUGIN_ROOT)
        if backup.exists():
            os.replace(backup, PLUGIN_ROOT)
        for path, original in catalog_snapshots.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                _atomic_write(path, original)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build or verify the deterministic dual-marketplace engineering-workflow package."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        version = _skill_version()
        if args.write:
            PLUGIN_ROOT.parent.mkdir(parents=True, exist_ok=True)
        temporary_parent = PLUGIN_ROOT.parent if args.write else None
        with tempfile.TemporaryDirectory(prefix="engineering-workflow-package-", dir=temporary_parent) as tmp:
            expected = Path(tmp) / PLUGIN_NAME
            _build_expected(expected, version)
            if args.write:
                write_package(expected)
                drift = []
            else:
                drift = _drift(expected)
        result = {
            "success": not drift,
            "mode": "write" if args.write else "check",
            "version": version,
            "plugin": PLUGIN_ROOT.relative_to(REPO_ROOT).as_posix(),
            "drift": drift,
        }
    except (OSError, PackageError) as exc:
        result = {
            "success": False,
            "mode": "write" if args.write else "check",
            "version": None,
            "plugin": PLUGIN_ROOT.relative_to(REPO_ROOT).as_posix(),
            "drift": [f"build_error:{type(exc).__name__}"],
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
