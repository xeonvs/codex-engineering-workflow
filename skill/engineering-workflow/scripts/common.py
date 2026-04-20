#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

CANONICAL_FILES = {
    "agents": "AGENTS.md",
    "plans": "PLANS.md",
    "principles": "docs/engineering/project_principles.md",
    "backlog": "docs/codex/TASKS_BACKLOG.md",
    "pitfalls": "docs/codex/AGENT_EXECUTION_PITFALLS.md",
}

OPTIONAL_FILES = {
    "adoption_note": "docs/codex/agent_practices_adoption.md",
    "migration_note": "docs/codex/exec_plan_migration_note.md",
}

LEGACY_COMPAT_FILES = [
    "CLAUDE.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
]

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "tmp",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

DOC_SUFFIXES = {".md", ".rst", ".txt"}
TEXT_LIKE_SUFFIXES = DOC_SUFFIXES | {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".php",
    ".rb",
    ".cs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".swift",
    ".scala",
    ".sh",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
}
TEXT_LIKE_FILENAMES = {
    "Dockerfile",
    "Makefile",
    "Jenkinsfile",
    "go.mod",
    "Gemfile",
    "Procfile",
    "Justfile",
    ".gitlab-ci.yml",
}

PROMPT_INJECTION_PATTERNS = [
    (
        "instruction_override",
        re.compile(r"\b(ignore|disregard|forget)\b.{0,80}\b(previous|prior|above)\b.{0,80}\binstructions?\b", re.IGNORECASE),
        "repo content tries to override higher-priority instructions",
    ),
    (
        "secrets_request",
        re.compile(r"\b(send|print|reveal|exfiltrate|upload|expose)\b.{0,80}\b(secret|token|credential|api key|password)\b", re.IGNORECASE),
        "repo content asks for secrets or credentials",
    ),
    (
        "remote_execution",
        re.compile(r"\b(curl|wget)\b.{0,40}\|\s*(sh|bash)\b", re.IGNORECASE),
        "repo content suggests piping remote content directly into a shell",
    ),
    (
        "data_exfiltration",
        re.compile(r"\b(upload|post|send)\b.{0,80}\b(to|into)\b.{0,80}\b(external|remote|server|webhook)\b", re.IGNORECASE),
        "repo content suggests exfiltrating data to an external destination",
    ),
]

WORKFLOW_OWNED_PATHS = set(CANONICAL_FILES.values()) | set(OPTIONAL_FILES.values()) | set(LEGACY_COMPAT_FILES)
WORKFLOW_OWNED_PREFIXES = ("docs/codex/", "docs/engineering/", "docs/exec-plans/", "docs/archive/")


def _iter_relevant_files(root: Path):
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def _is_text_like(path: Path) -> bool:
    return path.suffix.lower() in TEXT_LIKE_SUFFIXES or path.name in TEXT_LIKE_FILENAMES


def _classify_text_language(text: str) -> str:
    latin = 0
    cyrillic = 0
    for ch in text:
        if "A" <= ch <= "Z" or "a" <= ch <= "z":
            latin += 1
        elif "\u0400" <= ch <= "\u04FF":
            cyrillic += 1
    if latin == 0 and cyrillic == 0:
        return "unknown"
    bigger = max(latin, cyrillic)
    smaller = min(latin, cyrillic)
    if latin and cyrillic and smaller >= bigger * 0.35:
        return "mixed"
    return "cyrillic_dominant" if cyrillic > latin else "latin_dominant"


def _detect_language(texts: list[str]) -> str:
    per_text = {_classify_text_language(text) for text in texts if text.strip()}
    per_text.discard("unknown")
    if not per_text:
        return "unknown"
    if "mixed" in per_text or len(per_text) > 1:
        return "mixed"
    return per_text.pop()


def _classify_context_doc(root: Path, path: Path) -> dict | None:
    rel_path = path.relative_to(root)
    rel_text = str(rel_path)
    lower_rel = rel_text.lower()

    if path.suffix.lower() not in DOC_SUFFIXES:
        return None
    if rel_text in WORKFLOW_OWNED_PATHS or lower_rel.startswith(WORKFLOW_OWNED_PREFIXES):
        return None

    if lower_rel == "readme.md":
        return {
            "path": rel_text,
            "role": "repo_overview",
            "action": "leave_untouched",
            "reason": "existing repository overview should remain the entry point and be referenced from AGENTS.md",
        }

    return {
        "path": rel_text,
        "role": "context_doc",
        "action": "leave_untouched",
        "reason": "existing repo-specific documentation should remain separately owned and be linked from AGENTS.md when relevant",
    }


def _discover_context_docs(root: Path, relevant_files: list[Path]) -> list[dict]:
    discovered = []
    seen_paths = set()
    for path in relevant_files:
        doc = _classify_context_doc(root, path)
        if not doc or doc["path"] in seen_paths:
            continue
        seen_paths.add(doc["path"])
        discovered.append(doc)
    return sorted(discovered, key=lambda item: item["path"])


def _scan_prompt_injection_risks(root: Path, relevant_files: list[Path]) -> list[dict]:
    findings = []
    for path in relevant_files:
        if not _is_text_like(path):
            continue
        text = _read_text(path)
        if not text.strip():
            continue
        rel_path = str(path.relative_to(root))
        for name, pattern, reason in PROMPT_INJECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    {
                        "path": rel_path,
                        "type": name,
                        "reason": reason,
                        "match": match.group(0)[:160],
                    }
                )
                break
    return sorted(findings, key=lambda item: item["path"])


def classify_repo_maturity(
    root: Path,
    relevant_files: list[Path],
    doc_count: int,
    canonical_count: int,
    context_doc_count: int = 0,
    compatibility_count: int = 0,
) -> str:
    if not relevant_files:
        return "empty_directory"
    if (
        canonical_count >= 3
        or doc_count >= 5
        or len(relevant_files) >= 25
        or context_doc_count >= 2
        or compatibility_count > 0
    ):
        return "mature_repo"
    return "minimal_repo"


def classify_command_safety(command: str) -> str:
    lowered = command.strip().lower()
    read_only_patterns = [
        "git diff --check",
        "--help",
        " ls",
        "find ",
        "rg ",
        "sed ",
        "cat ",
    ]
    destructive_patterns = [
        " rm ",
        " mv ",
        " cp ",
        " touch ",
        " mkdir ",
        "git add",
        "git commit",
        "git push",
        "sed -i",
        "apply_patch",
    ]
    copy_only_patterns = [
        "compileall",
        "pytest",
        "unittest",
        "go test",
        "cargo test",
        "npm test",
        "npm run build",
        "ruff",
        "black",
        "prettier",
        "eslint",
        "mypy",
    ]

    if any(pattern in lowered for pattern in destructive_patterns):
        return "live_only"
    if any(pattern in lowered for pattern in copy_only_patterns):
        return "copy_only_safe"
    if lowered.startswith(("ls", "find", "rg", "sed", "cat")) or any(
        pattern in lowered for pattern in read_only_patterns
    ):
        return "read_only_safe"
    return "live_only"


def recommended_checks(root: Path) -> dict[str, list[str]]:
    relevant_files = list(_iter_relevant_files(root))
    read_only = ["git diff --check"]
    copy_only = []

    if (root / "Makefile").exists():
        read_only.append("make help")
    if any(path.suffix == ".py" for path in relevant_files) or any(
        (root / name).exists() for name in ("pyproject.toml", "requirements.txt", "requirements-dev.txt")
    ):
        copy_only.append("python -m compileall .")
    if (root / "package.json").exists():
        copy_only.append("npm test")

    return {
        "read_only_safe": read_only,
        "copy_only_safe": copy_only,
        "live_only": [],
    }


def audit_repo(root: Path) -> dict:
    relevant_files = list(_iter_relevant_files(root))
    docs = [path for path in relevant_files if path.suffix.lower() == ".md"]
    canonical_presence = {
        key: (root / rel_path).exists() for key, rel_path in CANONICAL_FILES.items()
    }
    optional_presence = {
        key: (root / rel_path).exists() for key, rel_path in OPTIONAL_FILES.items()
    }
    compat_presence = [rel for rel in LEGACY_COMPAT_FILES if (root / rel).exists()]
    context_docs = _discover_context_docs(root, relevant_files)
    prompt_injection_risks = _scan_prompt_injection_risks(root, relevant_files)

    language_sources = []
    for rel in list(CANONICAL_FILES.values()) + compat_presence:
        path = root / rel
        if path.exists():
            language_sources.append(_read_text(path))
    if not language_sources:
        language_sources = [_read_text(path) for path in docs[:5]]

    file_count = len(relevant_files)
    doc_count = len(docs)
    canonical_count = sum(1 for value in canonical_presence.values() if value)
    retained_history = any(
        (root / rel).exists() for rel in ("docs/exec-plans", "docs/archive")
    )
    repo_maturity = classify_repo_maturity(
        root,
        relevant_files,
        doc_count,
        canonical_count,
        context_doc_count=len(context_docs),
        compatibility_count=len(compat_presence),
    )

    return {
        "root": str(root.resolve()),
        "repo_maturity": repo_maturity,
        "file_count": file_count,
        "doc_count": doc_count,
        "canonical_files": canonical_presence,
        "optional_files": optional_presence,
        "compatibility_docs": compat_presence,
        "context_docs": context_docs,
        "prompt_injection_risks": prompt_injection_risks,
        "retained_history": retained_history,
        "dominant_language": _detect_language(language_sources),
        "recommended_validation": recommended_checks(root),
    }


def print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def find_placeholder_issues(text: str) -> list[str]:
    patterns = [
        r"\[TODO[:\]]",
        r"\{\{[^}]+\}\}",
    ]
    issues = []
    for pattern in patterns:
        if re.search(pattern, text):
            issues.append(pattern)
    return issues
