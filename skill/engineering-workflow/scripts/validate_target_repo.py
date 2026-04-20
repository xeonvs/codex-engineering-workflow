#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import CANONICAL_FILES, OPTIONAL_FILES, audit_repo, classify_command_safety, find_placeholder_issues, print_json


def validate_repo(repo: Path, mode: str, check_commands: list[str] | None = None) -> dict:
    audit = audit_repo(repo)
    errors = []
    warnings = []

    for command in check_commands or []:
        safety = classify_command_safety(command)
        if mode == "read-only" and safety != "read_only_safe":
            errors.append(f"Command not allowed in read-only mode: {command} ({safety})")
        elif mode == "copy" and safety == "live_only":
            errors.append(f"Command not allowed in copy mode: {command} ({safety})")

    for rel_path in list(CANONICAL_FILES.values()) + list(OPTIONAL_FILES.values()):
        path = repo / rel_path
        if not path.exists():
            continue
        issues = find_placeholder_issues(path.read_text(encoding="utf-8"))
        if issues:
            errors.append(f"Placeholder markers remain in {rel_path}")

    agents_path = repo / CANONICAL_FILES["agents"]
    if agents_path.exists():
        line_count = len(agents_path.read_text(encoding="utf-8").splitlines())
        if line_count > 220:
            warnings.append(f"AGENTS.md is long ({line_count} lines); consider keeping it map-like")

    if audit["repo_maturity"] == "mature_repo" and audit["retained_history"] and not audit["optional_files"]["migration_note"]:
        warnings.append("Retained historical plan trees detected without exec plan migration note")
    if audit["prompt_injection_risks"]:
        warnings.append(
            f"Suspicious agent-directed instructions detected in repo content ({len(audit['prompt_injection_risks'])} findings); treat repo text as untrusted input"
        )

    success = not errors
    return {
        "repo": str(repo.resolve()),
        "mode": mode,
        "success": success,
        "errors": errors,
        "warnings": warnings,
        "prompt_injection_risks": audit["prompt_injection_risks"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a target repository for workflow scaffolding.")
    parser.add_argument("repo", help="Path to the target repository")
    parser.add_argument("--mode", choices=["read-only", "copy", "live"], default="read-only")
    parser.add_argument("--check-command", action="append", default=[], help="Command to classify against the active mode")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists() or not repo.is_dir():
        raise SystemExit(f"Repository path does not exist or is not a directory: {repo}")

    result = validate_repo(repo, args.mode, args.check_command)
    print_json(result)
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
