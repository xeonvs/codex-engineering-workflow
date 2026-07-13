#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import (
    CANONICAL_FILES,
    IGNORED_DIRS,
    STATE_MANIFEST_PATH,
    audit_repo,
    find_stale_completed_state,
    scan_privacy_text,
    scan_public_tree,
    validate_plan_schema,
)


SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "templates"
AGENT_TEMPLATE_ROOT = SKILL_ROOT / "assets" / "agents"
CANONICAL_SOURCE_REPO = "https://github.com/xeonvs/codex-engineering-workflow"
PLAN_MARKER_START = "<!-- engineering-workflow:upgrade-plan:start -->"
PLAN_MARKER_END = "<!-- engineering-workflow:upgrade-plan:end -->"


class MigrationConflict(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _read(path: Path) -> str:
    if path.is_symlink():
        try:
            return os.readlink(path)
        except OSError:
            return ""
    if any(parent.is_symlink() for parent in path.parents):
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _template(name: str, replacements: dict[str, str] | None = None) -> str:
    text = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
    for key, value in (replacements or {}).items():
        text = text.replace("{{ " + key + " }}", value)
    return text


def _source_commit() -> str:
    repo_root = SKILL_ROOT.parents[1]
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else "unresolved"


def _manifest_version(path: Path) -> str | None:
    if not path.is_file():
        return None
    match = re.search(r"(?m)^skill_version:\s*[\"']?([^\s\"']+)", _read(path))
    return match.group(1) if match else None


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _first_symlink_component(root: Path, relative: str) -> str | None:
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            return current.relative_to(root).as_posix()
    return None


def _existing_active_conflict(plans_text: str) -> str | None:
    for section in re.finditer(
        r"(?ms)^## Active Plan:\s*(?P<title>[^\n]+)\n(?P<body>.*?)(?=^## |\Z)",
        plans_text,
    ):
        title = section.group("title").strip()
        if title.startswith("Engineering Workflow Upgrade"):
            continue
        status = re.search(r"(?m)^Status:\s*(planned|in_progress|blocked)\s*$", section.group("body"))
        if status:
            return f"Unrelated active plan must remain owned by its current task: {title}"
    return None


def _scan_contract_conflicts(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    patterns = (
        ("compressed_plan_rule", re.compile(r"\b(?:lightweight|compact|short)\s+(?:active\s+)?plan\b", re.IGNORECASE)),
        ("repo_change_without_plan", re.compile(r"\b(?:small|minor|quick)\s+changes?\b.{0,80}\b(?:without|no)\s+(?:a\s+)?plan\b", re.IGNORECASE)),
    )
    canonical_mutation_paths = {
        "PLANS.md",
        "AGENTS.md",
        *CANONICAL_FILES.values(),
        STATE_MANIFEST_PATH,
        ".codex/config.toml",
    }
    canonical_mutation_paths.update(
        f".codex/agents/{name}.toml" for name in ("utility", "explorer", "reviewer")
    )
    reported_symlinks = set()
    for relative in sorted(canonical_mutation_paths):
        symlink_component = _first_symlink_component(root, relative)
        if symlink_component and symlink_component not in reported_symlinks:
            reported_symlinks.add(symlink_component)
            findings.append(
                {
                    "type": "canonical_symlink",
                    "path": symlink_component,
                    "requires_decision": "true",
                }
            )
    agents_dir = root / ".codex" / "agents"
    if agents_dir.is_dir() and not _first_symlink_component(root, ".codex/agents"):
        for path in agents_dir.glob("*.toml"):
            if path.is_symlink():
                findings.append(
                    {
                        "type": "canonical_symlink",
                        "path": path.relative_to(root).as_posix(),
                        "requires_decision": "true",
                    }
                )
    for path in root.rglob("*"):
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if (
            not path.is_file()
            or any(part in IGNORED_DIRS for part in rel_parts)
            or path.suffix.lower() not in {".md", ".txt", ".rst"}
        ):
            continue
        text = _read(path)
        rel = path.relative_to(root).as_posix()
        for kind, pattern in patterns:
            if pattern.search(text):
                finding = {"type": kind, "path": rel}
                if rel in set(CANONICAL_FILES.values()):
                    finding["requires_decision"] = "true"
                findings.append(finding)
    plans = root / "PLANS.md"
    if plans.exists():
        stale = find_stale_completed_state(_read(plans))
        findings.extend({"type": "stale_completed_state", "path": "PLANS.md", "detail": item} for item in stale)
        conflict = _existing_active_conflict(_read(plans))
        if conflict:
            findings.append({"type": "unrelated_active_plan", "path": "PLANS.md", "detail": conflict})

    config = root / ".codex" / "config.toml"
    if config.exists() and not _first_symlink_component(root, ".codex/config.toml"):
        text = _read(config)
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            findings.append({"type": "invalid_codex_config", "path": ".codex/config.toml"})
        else:
            agents = data.get("agents", {}) if isinstance(data, dict) else {}
            if isinstance(agents, dict) and agents.get("max_depth") not in {None, 1}:
                findings.append({"type": "conflicting_max_depth", "path": ".codex/config.toml"})
            if isinstance(agents, dict) and isinstance(agents.get("max_depth"), int) and agents.get("max_depth", 0) > 1:
                findings.append({"type": "recursive_delegation", "path": ".codex/config.toml"})
            if "agents" in data and isinstance(agents, dict) and agents.get("max_depth") is None and not re.search(r"(?m)^\[agents\][ \t]*(?:#.*)?$", text):
                findings.append({"type": "unsupported_inline_agents", "path": ".codex/config.toml"})
    return findings


def _topology(root: Path) -> dict[str, Any]:
    nested_agents = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("AGENTS.md")
        if path.is_file() and path != root / "AGENTS.md" and ".git" not in path.parts
    )
    agents_dir = root / ".codex" / "agents"
    agent_configs = (
        sorted(path.relative_to(root).as_posix() for path in agents_dir.glob("*.toml"))
        if agents_dir.is_dir() and not _first_symlink_component(root, ".codex/agents")
        else []
    )
    return {
        "root_agents": _present(root / "AGENTS.md"),
        "nested_agents": nested_agents,
        "plans": _present(root / "PLANS.md"),
        "backlog": _present(root / CANONICAL_FILES["backlog"]),
        "pitfalls": _present(root / CANONICAL_FILES["pitfalls"]),
        "principles": _present(root / CANONICAL_FILES["principles"]),
        "codex_config": _present(root / ".codex" / "config.toml"),
        "agent_configs": agent_configs,
        "state_manifest": _present(root / STATE_MANIFEST_PATH),
        "legacy_plan_locations": [
            value for value in ("docs/exec-plans", "docs/archive/plans") if (root / value).exists()
        ],
    }


def _proposed_changes(root: Path, include_agent_config: bool) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    plans_action = "update" if _present(root / "PLANS.md") else "create"
    changes.append({"path": "PLANS.md", "action": plans_action, "reason": "materialize full migration plan first"})
    template_map = {
        "AGENTS.md": "AGENTS.md.tmpl",
        CANONICAL_FILES["principles"]: "project_principles.md.tmpl",
        CANONICAL_FILES["backlog"]: "TASKS_BACKLOG.md.tmpl",
        CANONICAL_FILES["pitfalls"]: "AGENT_EXECUTION_PITFALLS.md.tmpl",
    }
    for relative in template_map:
        if not _present(root / relative):
            changes.append({"path": relative, "action": "create", "reason": "missing canonical shared workflow file"})
    changes.append({
        "path": STATE_MANIFEST_PATH,
        "action": "update" if _present(root / STATE_MANIFEST_PATH) else "create",
        "reason": "record exact managed, shared, and protected paths",
    })
    if include_agent_config:
        changes.append({"path": ".codex/config.toml", "action": "structural_merge", "reason": "explicit runtime agent configuration request"})
        for name in ("utility", "explorer", "reviewer"):
            path = f".codex/agents/{name}.toml"
            if not _present(root / path):
                changes.append({"path": path, "action": "create", "reason": "explicit optional agent configuration request"})
    return changes


def build_migration_report(repo: Path, target_version: str, include_agent_config: bool = False) -> dict[str, Any]:
    root = repo.resolve()
    if not root.is_dir():
        raise MigrationConflict("missing_repository", "Target repository does not exist")
    audit = audit_repo(root)
    conflicts = _scan_contract_conflicts(root)
    blocking_types = {"unrelated_active_plan", "invalid_codex_config"}
    if include_agent_config:
        blocking_types.update({"conflicting_max_depth", "unsupported_inline_agents"})
    questions = []
    for finding in conflicts:
        if finding["type"] == "unrelated_active_plan":
            questions.append("How should the workflow migration be linked to the unrelated active PLANS.md task?")
        elif include_agent_config and finding["type"] == "conflicting_max_depth":
            questions.append("Should the existing explicit agents.max_depth decision be preserved or changed?")
        elif include_agent_config and finding["type"] == "unsupported_inline_agents":
            questions.append("How should the existing inline or dotted agents configuration be structurally migrated?")
        elif finding["type"] == "canonical_symlink":
            questions.append(f"Should the canonical symlink at {finding['path']} be retained, retargeted, or replaced?")
        elif finding.get("requires_decision") == "true":
            questions.append(f"Which source should own the contradictory planning rule in {finding['path']}?")
    proposed = _proposed_changes(root, include_agent_config)
    touched = {item["path"] for item in proposed}
    ownership = audit["ownership"]
    protected = sorted(set(ownership["protected"] + ownership["unknown"] + ownership["external_source_of_truth"]))
    privacy_findings = scan_public_tree(root)
    return {
        "success": not any(item["type"] in blocking_types or item.get("requires_decision") == "true" for item in conflicts),
        "mode": "plan",
        "repository": ".",
        "target_version": target_version,
        "current_workflow_version": (
            _manifest_version(root / STATE_MANIFEST_PATH)
            if not _first_symlink_component(root, STATE_MANIFEST_PATH)
            else None
        )
        or "unknown",
        "detected_topology": _topology(root),
        "ownership": ownership,
        "managed_paths": ownership["managed"],
        "shared_paths": ownership["shared"],
        "protected_paths": protected,
        "historical_paths": ownership["historical"],
        "conflicts": conflicts,
        "privacy_findings": privacy_findings,
        "proposed_changes": proposed,
        "untouched_files": sorted(path for path in protected if path not in touched),
        "required_user_questions": questions,
        "validation_plan": [
            "validate full PLANS.md schema and traceability",
            "parse workflow manifest and optional TOML",
            "verify protected files remain byte-identical",
            "scan changed public text for private paths and credential-like values",
        ],
        "rollback_plan": "Restore every pre-migration file snapshot in reverse mutation order; preserve a PLANS.md failure note if recovery is needed.",
        "include_agent_config": include_agent_config,
    }


def _migration_plan(target_version: str, include_agent_config: bool, *, done: bool = False, result: str = "Not run yet.") -> str:
    status = "done" if done else "in_progress"
    checkbox = "x" if done else " "
    req_status = "done" if done else "in_progress"
    today = datetime.now(timezone.utc).date().isoformat()
    resume = "No unfinished migration queue item remains." if done else "Start with WQ-02, the first unfinished queue item."
    return f"""{PLAN_MARKER_START}
## Active Plan: Engineering Workflow Upgrade {target_version}

Status: {status}
Owner: root
Last Updated: {today}
plan_schema_version: 1

### Goal

Upgrade only the target repository workflow layer to engineering-workflow {target_version} while preserving repository-owned documentation and configuration.

### Plan Origin

direct_execution

### Requested Scope

- Materialize the full migration plan before any other target write.
- Add missing canonical workflow structure, exact ownership state, and optional agent configuration only when explicitly selected.

### Requirement Traceability

| Requirement | Complete outcome | Source | Work queue | Acceptance or validation | Status |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Full migration plan is the first target write. | engineering-workflow contract | WQ-01 | Plan schema validates. | done |
| REQ-002 | Workflow-owned structure and manifest reach {target_version} without modifying protected docs. | migration report | WQ-02 | Protected snapshots agree and manifest parses. | {req_status} |
| REQ-003 | Runtime agent configuration follows the explicit selection. | user invocation | WQ-03 | Config is {'structurally merged' if include_agent_config else 'untouched'}. | {req_status} |

### Explicit Non-Goals

- Do not rewrite product, domain, architecture, operations, QA, release, security, or external-tracker sources.

### Constraints

- Unknown ownership remains protected; no shared file is replaced wholesale; rollback must remain bounded.

### Inputs And Sources

- Canonical source: {CANONICAL_SOURCE_REPO}
- Read-only target audit and migration report generated before apply.

### User Decisions And Answers

- Runtime agent configuration requested: {'yes' if include_agent_config else 'no'}.

### Completed Baseline State

- [x] WQ-00 — Target topology, ownership, conflicts, privacy signals, and proposed changes were audited without executing repository code.

### Current Work Queue

- [x] WQ-01 — Materialize this full plan for REQ-001 as the first write.
- [{checkbox}] WQ-02 — Apply and validate canonical workflow/manifest changes for REQ-002.
- [{checkbox}] WQ-03 — Preserve or structurally merge runtime configuration for REQ-003.

### Locked Decisions

- Protected and unknown files remain untouched unless a later explicit decision changes ownership.

### Verification

- REQ-001: structural plan validation.
- REQ-002: manifest, ownership, privacy, and protected-file checks.
- REQ-003: TOML parse and exact configuration diff when selected.

### Latest Validation Results

- {result}

### Risks And Recovery

- Risk: partial migration. Recovery: restore captured file snapshots in reverse mutation order and record the exact failure.

### Resume Point

- {resume}

### Plan Fidelity Check

- [x] Outcomes, source URL, invocation decision, constraints, queue, validation, recovery, and resume state are preserved without compression.

### Reconciliation Check

- [{'x' if done else ' '}] Requirements, queue, validation, working tree, manifest, and statuses agree; completed text has no stale next-work state.

### Pre-Commit Closure

- [{'x' if done else ' '}] The migration plan reflects its post-apply state and no promoted backlog state is stale.

### Handoff Notes

- {'Migration complete; review the reported file and configuration diffs.' if done else 'Continue only from the first unfinished queue item after reconciling target state.'}
{PLAN_MARKER_END}
"""


def _put_plan_first(existing: str, plan: str) -> str:
    if PLAN_MARKER_START in existing and PLAN_MARKER_END in existing:
        return re.sub(
            re.escape(PLAN_MARKER_START) + r".*?" + re.escape(PLAN_MARKER_END),
            plan.strip(),
            existing,
            count=1,
            flags=re.DOTALL,
        ).rstrip() + "\n"
    if not existing.strip():
        return "# Execution Plans\n\n" + plan
    lines = existing.splitlines(keepends=True)
    if lines and lines[0].startswith("# "):
        return lines[0].rstrip() + "\n\n" + plan + "\n" + "".join(lines[1:]).lstrip()
    return "# Execution Plans\n\n" + plan + "\n" + existing


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _merge_codex_config(text: str) -> tuple[str, str]:
    try:
        parsed = tomllib.loads(text) if text.strip() else {}
    except tomllib.TOMLDecodeError as exc:
        raise MigrationConflict("invalid_codex_config", "Existing .codex/config.toml is invalid TOML") from exc
    agents = parsed.get("agents", {}) if isinstance(parsed, dict) else {}
    if isinstance(agents, dict) and agents.get("max_depth") not in {None, 1}:
        raise MigrationConflict("conflicting_max_depth", "Existing agents.max_depth requires an explicit decision")
    if isinstance(agents, dict) and agents.get("max_depth") == 1:
        return text, ""
    header = re.search(r"(?m)^\[agents\][ \t]*(?:#.*)?$", text)
    if "agents" in parsed and isinstance(agents, dict) and header is None:
        raise MigrationConflict("unsupported_inline_agents", "Inline or dotted agents configuration requires an explicit migration decision")
    if header:
        updated = text[: header.end()] + "\nmax_depth = 1" + text[header.end() :]
    else:
        separator = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
        updated = text + separator + "[agents]\nmax_depth = 1\n"
    diff = "".join(
        difflib.unified_diff(
            text.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile="a/.codex/config.toml",
            tofile="b/.codex/config.toml",
            n=0,
        )
    )
    return updated, diff


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _manifest_text(
    target_version: str,
    protected_paths: list[str],
    shared_paths: list[str],
    include_agent_config: bool,
) -> str:
    applied = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        "schema_version: 1",
        "skill_name: engineering-workflow",
        f"skill_version: {_yaml_quote(target_version)}",
        f"applied_at: {_yaml_quote(applied)}",
        "mode: upgrade_target_workflow",
        f"source_repo: {_yaml_quote(CANONICAL_SOURCE_REPO)}",
        f"source_ref: {_yaml_quote(target_version)}",
        f"source_commit: {_yaml_quote(_source_commit())}",
        "managed_paths:",
        f"  - {STATE_MANIFEST_PATH}",
        "shared_paths:",
    ]
    lines.extend(f"  - {_yaml_quote(path)}" for path in sorted(shared_paths))
    lines.append("protected_paths:")
    lines.extend(f"  - {_yaml_quote(path)}" for path in sorted(protected_paths))
    if not protected_paths:
        lines[-1] = "protected_paths: []"
    lines.extend(
        [
            f"runtime_agent_config_managed: {'true' if include_agent_config else 'false'}",
            "planning_contract_version: 1",
            "orchestration_contract_version: 1",
        ]
    )
    return "\n".join(lines) + "\n"


def apply_migration(repo: Path, target_version: str, include_agent_config: bool = False) -> dict[str, Any]:
    root = repo.resolve()
    report = build_migration_report(root, target_version, include_agent_config)
    if report["required_user_questions"]:
        return {**report, "success": False, "mode": "apply", "update_status": "question_required", "mutation_log": []}
    if not report["success"]:
        return {**report, "success": False, "mode": "apply", "update_status": "conflict", "mutation_log": []}

    snapshots: dict[Path, bytes | None] = {}
    mutation_log: list[str] = []
    created: list[str] = []
    changed: list[str] = []
    config_diff = ""
    protected_snapshots = {
        relative: (root / relative).read_bytes()
        for relative in report["protected_paths"]
        if (root / relative).is_file() and not (root / relative).is_symlink()
    }

    def write(relative: str, text: str) -> None:
        path = root / relative
        if path not in snapshots:
            snapshots[path] = path.read_bytes() if path.exists() else None
        before = _read(path) if path.exists() else None
        _atomic_write(path, text)
        mutation_log.append(relative)
        (created if before is None else changed).append(relative)

    plans_path = root / "PLANS.md"
    initial_plan = _migration_plan(target_version, include_agent_config)
    write("PLANS.md", _put_plan_first(_read(plans_path), initial_plan))

    try:
        template_map = {
            "AGENTS.md": (
                "AGENTS.md.tmpl",
                {
                    "entrypoint_hint": "README.md" if (root / "README.md").exists() else ".",
                    "subsystem_hint": "src/" if (root / "src").exists() else ".",
                },
            ),
            CANONICAL_FILES["principles"]: ("project_principles.md.tmpl", {}),
            CANONICAL_FILES["backlog"]: ("TASKS_BACKLOG.md.tmpl", {}),
            CANONICAL_FILES["pitfalls"]: ("AGENT_EXECUTION_PITFALLS.md.tmpl", {}),
        }
        for relative, (name, replacements) in template_map.items():
            if not _present(root / relative):
                write(relative, _template(name, replacements))

        if include_agent_config:
            config_path = root / ".codex" / "config.toml"
            merged, config_diff = _merge_codex_config(_read(config_path))
            if merged != _read(config_path):
                write(".codex/config.toml", merged)
            for name in ("utility", "explorer", "reviewer"):
                relative = f".codex/agents/{name}.toml"
                if not _present(root / relative):
                    write(relative, (AGENT_TEMPLATE_ROOT / f"{name}.toml.tmpl").read_text(encoding="utf-8"))

        shared_paths = [path for path in CANONICAL_FILES.values() if _present(root / path)]
        if include_agent_config:
            shared_paths.extend(
                path.relative_to(root).as_posix()
                for path in (root / ".codex" / "agents").glob("*.toml")
            )
            if _present(root / ".codex" / "config.toml"):
                shared_paths.append(".codex/config.toml")
        manifest = _manifest_text(
            target_version,
            report["protected_paths"],
            sorted(set(shared_paths)),
            include_agent_config,
        )
        if scan_privacy_text(manifest):
            raise MigrationConflict("unsafe_manifest", "Generated manifest contains private data")
        write(STATE_MANIFEST_PATH, manifest)

        plan_issues = validate_plan_schema(_read(plans_path), declared_external_sources=True)
        if plan_issues:
            raise MigrationConflict("invalid_generated_plan", "; ".join(plan_issues))
        if include_agent_config:
            tomllib.loads(_read(root / ".codex" / "config.toml"))
            for path in (root / ".codex" / "agents").glob("*.toml"):
                tomllib.loads(_read(path))

        for relative, expected in protected_snapshots.items():
            path = root / relative
            if not path.is_file() or path.read_bytes() != expected:
                raise MigrationConflict("protected_file_changed", f"Protected file changed during migration: {relative}")

        final_result = "Plan schema, ownership manifest, privacy, protected-file, and optional TOML checks passed."
        final_plan = _migration_plan(target_version, include_agent_config, done=True, result=final_result)
        write("PLANS.md", _put_plan_first(_read(plans_path), final_plan))
    except Exception as exc:
        for path, data in reversed(list(snapshots.items())):
            if path == plans_path:
                continue
            if data is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        failure = _migration_plan(target_version, include_agent_config, result=f"Apply failed and non-plan files were restored: {type(exc).__name__}.")
        _atomic_write(plans_path, _put_plan_first(_read(plans_path), failure))
        return {
            **report,
            "success": False,
            "mode": "apply",
            "update_status": "rolled_back",
            "errors": [{"type": type(exc).__name__, "message": str(exc)}],
            "mutation_log": mutation_log,
            "config_diff": config_diff,
        }

    return {
        **report,
        "success": True,
        "mode": "apply",
        "update_status": "updated",
        "created_files": sorted(set(created)),
        "changed_files": sorted(set(changed)),
        "mutation_log": mutation_log,
        "config_diff": config_diff,
        "validation_result": {"success": True, "plan_schema": True, "privacy": True, "toml": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or apply a conservative engineering-workflow migration.")
    parser.add_argument("--repo", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--target-version", default="0.5.0")
    parser.add_argument("--include-agent-config", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()

    try:
        result = (
            apply_migration(Path(args.repo), args.target_version, args.include_agent_config)
            if args.apply
            else build_migration_report(Path(args.repo), args.target_version, args.include_agent_config)
        )
    except MigrationConflict as exc:
        result = {"success": False, "mode": "apply" if args.apply else "plan", "errors": [{"code": exc.code, "message": str(exc)}]}
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result.get('mode')}: {'ok' if result.get('success') else 'failed'}")
        for item in result.get("proposed_changes", []):
            print(f"{item['action']}: {item['path']}")
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
