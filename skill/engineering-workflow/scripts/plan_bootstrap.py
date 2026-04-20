#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import CANONICAL_FILES, OPTIONAL_FILES, audit_repo, print_json


def build_plan(repo: Path) -> dict:
    audit = audit_repo(repo)
    mode = "greenfield_scaffold" if audit["repo_maturity"] == "empty_directory" else "conservative_merge"
    actions = []

    for key, rel_path in CANONICAL_FILES.items():
        action = "update_in_place" if audit["canonical_files"][key] else "create"
        actions.append({"path": rel_path, "action": action})

    optional_actions = []
    if audit["repo_maturity"] == "mature_repo" and audit["retained_history"]:
        optional_actions.append(
            {"path": OPTIONAL_FILES["migration_note"], "action": "create", "reason": "retained historical plan topology"}
        )

    if audit["repo_maturity"] == "mature_repo" and (
        audit["retained_history"] or audit["compatibility_docs"]
    ):
        optional_actions.append(
            {"path": OPTIONAL_FILES["adoption_note"], "action": "create", "reason": "record adopted and adapted workflow practices"}
        )

    questions = []
    if audit["dominant_language"] == "mixed":
        questions.append("language_choice")
    if audit["retained_history"]:
        questions.append("retained_history_policy")
    if audit["compatibility_docs"]:
        questions.append("compatibility_shim_policy")
    if audit["recommended_validation"]["copy_only_safe"]:
        questions.append("validation_mode")

    notes = []
    if audit["context_docs"]:
        notes.append("Keep existing repo-specific docs as their own sources of truth; reference them from AGENTS.md instead of rewriting them.")

    return {
        "repo": str(repo.resolve()),
        "recommended_mode": mode,
        "repo_maturity": audit["repo_maturity"],
        "artifact_actions": actions,
        "optional_artifact_actions": optional_actions,
        "protected_doc_actions": audit["context_docs"],
        "questions": questions,
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce a workflow bootstrap plan for a repository.")
    parser.add_argument("repo", help="Path to the target repository")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists() or not repo.is_dir():
        raise SystemExit(f"Repository path does not exist or is not a directory: {repo}")

    print_json(build_plan(repo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
