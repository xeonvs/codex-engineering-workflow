#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable


PLAN_SCHEMA_VERSION = 1
PLAN_ORIGINS = {
    "plan_mode_approved",
    "direct_execution",
    "resumed",
    "backlog_promotion",
    "external_handoff",
}
REQUIRED_PLAN_SECTIONS = (
    "Goal",
    "Plan Origin",
    "Requested Scope",
    "Requirement Traceability",
    "Explicit Non-Goals",
    "Constraints",
    "Inputs And Sources",
    "User Decisions And Answers",
    "Completed Baseline State",
    "Current Work Queue",
    "Locked Decisions",
    "Verification",
    "Latest Validation Results",
    "Risks And Recovery",
    "Resume Point",
    "Plan Fidelity Check",
    "Reconciliation Check",
    "Pre-Commit Closure",
    "Handoff Notes",
)

CANONICAL_FILES = {
    "agents": "AGENTS.md",
    "plans": "PLANS.md",
    "principles": "docs/engineering/project_principles.md",
    "backlog": "docs/codex/TASKS_BACKLOG.md",
    "pitfalls": "docs/codex/AGENT_EXECUTION_PITFALLS.md",
}
STATE_MANIFEST_PATH = "docs/codex/ENGINEERING_WORKFLOW_STATE.yaml"
OPTIONAL_FILES = {
    "adoption_note": "docs/codex/agent_practices_adoption.md",
    "migration_note": "docs/codex/exec_plan_migration_note.md",
}
LEGACY_COMPAT_FILES = (
    "CLAUDE.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
)
SUPPORTED_ARCHIVE_PREFIXES = (
    "docs/archive/plans/",
    "docs/archive/backlog/",
    "docs/exec-plans/",
)
MANAGED_MARKER_START = "<!-- engineering-workflow:managed:start -->"
MANAGED_MARKER_END = "<!-- engineering-workflow:managed:end -->"

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "node_modules",
    "vendor",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
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
    ".tmpl",
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
    ".gitignore",
}

PROMPT_INJECTION_PATTERNS = (
    (
        "instruction_override",
        re.compile(
            r"\b(ignore|disregard|forget)\b.{0,80}\b(previous|prior|above)\b.{0,80}\binstructions?\b",
            re.IGNORECASE,
        ),
        "repo content tries to override higher-priority instructions",
    ),
    (
        "secrets_request",
        re.compile(
            r"\b(send|print|reveal|exfiltrate|upload|expose)\b.{0,80}\b(secret|token|credential|api key|password)\b",
            re.IGNORECASE,
        ),
        "repo content asks for secrets or credentials",
    ),
    (
        "remote_execution",
        re.compile(r"\b(curl|wget)\b.{0,40}\|\s*(sh|bash)\b", re.IGNORECASE),
        "repo content suggests piping remote content directly into a shell",
    ),
    (
        "data_exfiltration",
        re.compile(
            r"\b(upload|post|send)\b.{0,80}\b(to|into)\b.{0,80}\b(external|remote|server|webhook)\b",
            re.IGNORECASE,
        ),
        "repo content suggests exfiltrating data to an external destination",
    ),
)

PRIVACY_PATTERNS = {
    "macos_user_path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "linux_user_path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "windows_user_path": re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9._ -]+\\"),
    "file_url": re.compile(r"\bfile:" + r"//", re.IGNORECASE),
    "private_ssh_key_path": re.compile(
        r"(?:~|/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|[A-Za-z]:\\Users\\[^\\]+)[/\\]\.ssh[/\\](?:id_rsa|id_ed25519|id_ecdsa|id_dsa)",
        re.IGNORECASE,
    ),
    "private_key_material": re.compile(
        r"BEGIN (?:RSA |OPENSSH |EC )?" + r"PRIVATE KEY",
        re.IGNORECASE,
    ),
    "internal_hostname": re.compile(r"\b[a-zA-Z0-9.-]+\.(?:internal|corp|local)\b"),
    "credential_like_assignment": re.compile(
        r"\b(api[_-]?key|access[_-]?token|auth[_-]?token|token|secret|password|passwd)\b\s*[:=]\s*['\"]?[^\s'\";,]{8,}",
        re.IGNORECASE,
    ),
    "known_token_prefix": re.compile(
        r"(?:ghp" + r"_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk" + r"-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})"
    ),
    "ssh_repository_url": re.compile(
        r"(?:ssh:" + r"//[^\s]+|git" + r"@[^\s:]+:[^\s]+)",
        re.IGNORECASE,
    ),
    "url_with_credentials": re.compile(r"https?://[^\s/@:]+:[^\s/@]+@[^\s/]+", re.IGNORECASE),
}


def _iter_relevant_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        if path.is_symlink():
            yield path
            continue
        if path.is_file():
            yield path


def _read_text(path: Path) -> str:
    if path.is_symlink():
        try:
            return os.readlink(path)
        except OSError:
            return ""
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if b"\x00" in data:
        return ""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return ""


def _is_text_like(path: Path) -> bool:
    if path.suffix.lower() in TEXT_LIKE_SUFFIXES or path.name in TEXT_LIKE_FILENAMES:
        return True
    return bool(_read_text(path))


def iter_public_text_files(root: Path) -> Iterable[Path]:
    """Yield tracked public text files, or all non-ignored text files without Git."""
    candidates: list[Path] = []
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            check=False,
            capture_output=True,
        )
        if result.returncode == 0:
            candidates = [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]
    if not candidates:
        candidates = list(_iter_relevant_files(root))

    for path in candidates:
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in IGNORED_DIRS for part in rel.parts):
            continue
        if (path.is_symlink() or path.is_file()) and _is_text_like(path):
            yield path


def scan_privacy_text(text: str) -> list[dict[str, int | str]]:
    """Return categories and line numbers without echoing sensitive values."""
    issues: list[dict[str, int | str]] = []
    for name, pattern in PRIVACY_PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            issues.append({"type": name, "line": line})
    return issues


def scan_public_tree(root: Path) -> list[dict[str, int | str]]:
    issues: list[dict[str, int | str]] = []
    for path in iter_public_text_files(root):
        text = _read_text(path)
        if not text:
            continue
        rel = path.relative_to(root).as_posix()
        for issue in scan_privacy_text(text):
            issues.append({"path": rel, **issue})
    return issues


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


def _normalize_managed_path(raw: str) -> str | None:
    value = raw.strip().strip("\"'").replace("\\", "/")
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:/", value):
        return None
    parts = Path(value).parts
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return Path(*parts).as_posix()


def load_managed_paths(root: Path) -> set[str]:
    manifest = root / STATE_MANIFEST_PATH
    if not manifest.exists():
        return set()
    text = _read_text(manifest)
    managed: set[str] = set()
    active = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not raw_line.startswith((" ", "\t")):
            active = stripped.startswith("managed_paths:")
            continue
        if active and stripped.startswith("-"):
            normalized = _normalize_managed_path(stripped[1:].strip())
            if normalized:
                managed.add(normalized)
        elif active and stripped and not stripped.startswith("#"):
            active = False
    return managed


def _contains_managed_section(path: Path) -> bool:
    text = _read_text(path)
    return MANAGED_MARKER_START in text and MANAGED_MARKER_END in text


def classify_workflow_artifact(root: Path, path: Path, managed_paths: set[str] | None = None) -> str:
    rel = path.relative_to(root).as_posix()
    lower = rel.lower()
    managed_paths = managed_paths if managed_paths is not None else load_managed_paths(root)

    if rel == STATE_MANIFEST_PATH or rel in managed_paths or _contains_managed_section(path):
        return "managed"
    if any(lower.startswith(prefix) for prefix in SUPPORTED_ARCHIVE_PREFIXES):
        return "historical"
    if rel in CANONICAL_FILES.values() or rel in OPTIONAL_FILES.values() or rel in LEGACY_COMPAT_FILES:
        return "shared"
    if lower == "readme.md" or lower.endswith("/readme.md"):
        return "external_source_of_truth"
    if path.suffix.lower() in DOC_SUFFIXES:
        protected_words = (
            "architecture",
            "product",
            "security",
            "policy",
            "runbook",
            "release",
            "operations",
            "benchmark",
            "test-strategy",
            "qa/",
        )
        if any(word in lower for word in protected_words):
            return "protected"
        return "unknown"
    if lower in {".codex/config.toml"} or lower.startswith(".codex/agents/"):
        return "shared"
    return "unknown"


def _context_doc_reason(classification: str) -> str:
    reasons = {
        "managed": "path is declared by the workflow state manifest or explicit managed-section markers",
        "shared": "canonical workflow or compatibility path may contain repository-owned content and requires a narrow merge",
        "protected": "domain, product, architecture, QA, security, or operational documentation remains repository-owned",
        "external_source_of_truth": "repository overview or external-owner documentation should be indexed rather than absorbed",
        "historical": "supported historical path remains non-canonical retained context",
        "unknown": "ownership is not proven; keep protected until repository evidence or user direction resolves it",
    }
    return reasons[classification]


def discover_workflow_artifacts(root: Path, relevant_files: list[Path] | None = None) -> list[dict[str, str]]:
    files = relevant_files if relevant_files is not None else list(_iter_relevant_files(root))
    managed_paths = load_managed_paths(root)
    artifacts: list[dict[str, str]] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() not in DOC_SUFFIXES and rel not in {
            STATE_MANIFEST_PATH,
            ".codex/config.toml",
        } and not rel.startswith(".codex/agents/"):
            continue
        classification = classify_workflow_artifact(root, path, managed_paths)
        artifacts.append(
            {
                "path": rel,
                "classification": classification,
                "reason": _context_doc_reason(classification),
            }
        )
    return sorted(artifacts, key=lambda item: item["path"])


def _discover_context_docs(root: Path, relevant_files: list[Path]) -> list[dict[str, str]]:
    results = []
    for item in discover_workflow_artifacts(root, relevant_files):
        if item["classification"] in {"managed", "shared", "historical"}:
            continue
        action = "leave_untouched"
        results.append(
            {
                "path": item["path"],
                "role": item["classification"],
                "action": action,
                "reason": item["reason"],
            }
        )
    return results


def _scan_prompt_injection_risks(root: Path, relevant_files: list[Path]) -> list[dict[str, str]]:
    findings = []
    for path in relevant_files:
        if not _is_text_like(path):
            continue
        text = _read_text(path)
        if not text.strip():
            continue
        rel_path = path.relative_to(root).as_posix()
        for name, pattern, reason in PROMPT_INJECTION_PATTERNS:
            if pattern.search(text):
                findings.append({"path": rel_path, "type": name, "reason": reason})
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
    del root
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


_SHELL_CONTROL = re.compile(r"(?:&&|\|\||[;\n\r]|(?<!\\)\||[<>`]|\$\(|\$\{|\$[A-Za-z_(])")
_DESTRUCTIVE_EXECUTABLES = {
    "rm",
    "mv",
    "cp",
    "touch",
    "mkdir",
    "rmdir",
    "chmod",
    "chown",
    "curl",
    "wget",
    "ssh",
    "scp",
    "rsync",
}
_COPY_ONLY_EXECUTABLES = {
    "make",
    "pytest",
    "ruff",
    "black",
    "prettier",
    "eslint",
    "mypy",
    "npm",
    "npx",
    "pnpm",
    "yarn",
    "bun",
    "pip",
    "pip3",
    "poetry",
    "uv",
    "cargo",
    "go",
    "mvn",
    "gradle",
    "gradlew",
    "bundle",
    "rake",
    "cmake",
    "ninja",
    "bash",
    "sh",
    "zsh",
}
_SAFE_GIT_SUBCOMMANDS = {"status", "diff", "ls-files", "log", "show", "rev-parse", "grep"}
_MUTATING_GIT_SUBCOMMANDS = {
    "add",
    "am",
    "apply",
    "branch",
    "checkout",
    "cherry-pick",
    "clean",
    "commit",
    "fetch",
    "merge",
    "pull",
    "push",
    "rebase",
    "reset",
    "restore",
    "revert",
    "rm",
    "switch",
    "tag",
    "worktree",
}


def _has_unsafe_find_action(tokens: list[str]) -> bool:
    unsafe = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf"}
    return any(token in unsafe for token in tokens[1:])


def classify_command_safety(command: str) -> str:
    """Classify a single command without trusting safe-looking prefixes."""
    stripped = command.strip()
    if not stripped or _SHELL_CONTROL.search(stripped):
        return "live_only"
    try:
        tokens = shlex.split(stripped, posix=True)
    except ValueError:
        return "live_only"
    if not tokens:
        return "live_only"

    executable = Path(tokens[0]).name.lower()
    if executable in _DESTRUCTIVE_EXECUTABLES:
        return "live_only"
    if executable == "git":
        if len(tokens) < 2 or tokens[1].startswith("-"):
            return "live_only"
        subcommand = tokens[1].lower()
        if subcommand in _MUTATING_GIT_SUBCOMMANDS:
            return "live_only"
        if subcommand not in _SAFE_GIT_SUBCOMMANDS:
            return "live_only"
        if any(token.startswith(("--output", "--exec-path")) for token in tokens[2:]):
            return "live_only"
        return "read_only_safe"

    if executable in {"ls", "cat", "head", "tail", "wc", "pwd", "stat", "readlink", "test"}:
        return "read_only_safe"
    if executable in {"rg", "grep"}:
        if any(token in {"--pre", "--pre-glob"} or token.startswith("--pre=") for token in tokens[1:]):
            return "live_only"
        return "read_only_safe"
    if executable == "sed":
        return "live_only"
    if executable == "find":
        return "live_only" if _has_unsafe_find_action(tokens) else "read_only_safe"

    if executable in {"python", "python3"}:
        if "-c" in tokens or "-" in tokens[1:2]:
            return "live_only"
        return "copy_only_safe"
    if executable in _COPY_ONLY_EXECUTABLES:
        return "copy_only_safe"
    return "live_only"


def recommended_checks(root: Path) -> dict[str, list[str]]:
    relevant_files = list(_iter_relevant_files(root))
    read_only = ["git status --short", "git diff --check", "git ls-files"]
    copy_only: list[str] = []
    if (root / "Makefile").exists():
        copy_only.append("make help")
    if any(path.suffix == ".py" for path in relevant_files) or any(
        (root / name).exists()
        for name in ("pyproject.toml", "requirements.txt", "requirements-dev.txt")
    ):
        copy_only.append("python -m compileall .")
    if (root / "package.json").exists():
        copy_only.append("npm test")
    return {"read_only_safe": read_only, "copy_only_safe": copy_only, "live_only": []}


def _minimal_disposable_env(temp_root: Path) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(temp_root / "home"),
        "TMPDIR": str(temp_root / "tmp"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_NO_INDEX": "1",
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "ALL_PROXY": "http://127.0.0.1:9",
        "NO_PROXY": "",
        "no_proxy": "",
    }
    Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
    Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
    return env


def _external_symlinks(root: Path) -> list[str]:
    external = []
    resolved_root = root.resolve()
    for path in root.rglob("*"):
        if not path.is_symlink():
            continue
        try:
            resolved = path.resolve(strict=False)
        except (OSError, RuntimeError):
            external.append(path.relative_to(root).as_posix())
            continue
        if not resolved.is_relative_to(resolved_root):
            external.append(path.relative_to(root).as_posix())
    return sorted(external)


def _network_guard_prefix(temp_root: Path) -> list[str] | None:
    sandbox_exec = Path("/usr/bin/sandbox-exec")
    if sys.platform == "darwin" and sandbox_exec.exists():
        allowed_root = str(temp_root.resolve()).replace("\\", "\\\\").replace('"', '\\"')
        real_home = str(Path.home()).replace("\\", "\\\\").replace('"', '\\"')
        profile = (
            "(version 1) "
            "(allow default) "
            "(deny network*) "
            f'(deny file-write* (require-not (subpath "{allowed_root}"))) '
            f'(deny file-read* (require-all (subpath "{real_home}") (require-not (subpath "{allowed_root}"))))'
        )
        return [str(sandbox_exec), "-p", profile]
    return None


def _intrinsically_offline(tokens: list[str]) -> bool:
    executable = Path(tokens[0]).name.lower()
    return executable in {"python", "python3"} and tokens[1:3] == ["-m", "compileall"]


def run_in_disposable_copy(repo: Path, commands: list[str], timeout_seconds: int = 300) -> list[dict]:
    """Run copy-only commands in an isolated copy with a minimal credential-free env."""
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="engineering-workflow-verify-") as temp_name:
        temp_root = Path(temp_name)
        copy_root = temp_root / "repo"
        try:
            shutil.copytree(
                repo,
                copy_root,
                ignore=shutil.ignore_patterns(*IGNORED_DIRS),
                symlinks=True,
            )
        except OSError:
            return [
                {
                    "command": command,
                    "status": "rejected",
                    "reason": "repository could not be copied safely",
                }
                for command in commands
            ]
        env = _minimal_disposable_env(temp_root)
        unsafe_links = _external_symlinks(copy_root)
        if unsafe_links:
            for command in commands:
                results.append(
                    {
                        "command": command,
                        "status": "rejected",
                        "reason": f"disposable copy contains {len(unsafe_links)} external symlink(s)",
                    }
                )
            return results
        network_guard = _network_guard_prefix(temp_root)
        for command in commands:
            safety = classify_command_safety(command)
            if safety != "copy_only_safe":
                results.append(
                    {"command": command, "status": "rejected", "reason": f"expected copy_only_safe, got {safety}"}
                )
                continue
            tokens = shlex.split(command)
            executable = Path(tokens[0]).name.lower()
            if executable in {"pip", "pip3", "npm", "npx", "pnpm", "yarn", "bun", "cargo", "go"}:
                results.append(
                    {"command": command, "status": "rejected", "reason": "network-capable package command requires an explicit offline wrapper"}
                )
                continue
            if network_guard is None and not _intrinsically_offline(tokens):
                results.append(
                    {
                        "command": command,
                        "status": "rejected",
                        "reason": "command requires OS network isolation or an explicit offline wrapper",
                    }
                )
                continue
            if executable in {"python", "python3"}:
                tokens[0] = sys.executable
            execution_tokens = [*network_guard, *tokens] if network_guard else tokens
            try:
                completed = subprocess.run(
                    execution_tokens,
                    cwd=copy_root,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                results.append({"command": command, "status": "timeout", "timeout_seconds": timeout_seconds})
                continue
            results.append(
                {
                    "command": command,
                    "status": "passed" if completed.returncode == 0 else "failed",
                    "returncode": completed.returncode,
                    "network_policy": "os_sandbox_deny" if network_guard else "intrinsic_offline",
                }
            )
    return results


def audit_repo(root: Path) -> dict:
    relevant_files = list(_iter_relevant_files(root))
    docs = [path for path in relevant_files if path.suffix.lower() in DOC_SUFFIXES]
    canonical_presence = {key: (root / rel_path).exists() for key, rel_path in CANONICAL_FILES.items()}
    optional_presence = {key: (root / rel_path).exists() for key, rel_path in OPTIONAL_FILES.items()}
    compat_presence = [rel for rel in LEGACY_COMPAT_FILES if (root / rel).exists()]
    workflow_artifacts = discover_workflow_artifacts(root, relevant_files)
    context_docs = _discover_context_docs(root, relevant_files)
    prompt_injection_risks = _scan_prompt_injection_risks(root, relevant_files)

    language_sources = []
    for rel in list(CANONICAL_FILES.values()) + compat_presence:
        path = root / rel
        if path.exists():
            language_sources.append(_read_text(path))
    if not language_sources:
        language_sources = [_read_text(path) for path in docs[:5]]

    retained_history = any((root / rel).exists() for rel in ("docs/exec-plans", "docs/archive"))
    repo_maturity = classify_repo_maturity(
        root,
        relevant_files,
        len(docs),
        sum(1 for value in canonical_presence.values() if value),
        context_doc_count=len(context_docs),
        compatibility_count=len(compat_presence),
    )
    classified_paths = {
        name: [item["path"] for item in workflow_artifacts if item["classification"] == name]
        for name in ("managed", "shared", "protected", "external_source_of_truth", "historical", "unknown")
    }

    return {
        "root": str(root.resolve()),
        "repo_maturity": repo_maturity,
        "file_count": len(relevant_files),
        "doc_count": len(docs),
        "canonical_files": canonical_presence,
        "optional_files": optional_presence,
        "state_manifest": (root / STATE_MANIFEST_PATH).exists(),
        "compatibility_docs": compat_presence,
        "workflow_artifacts": workflow_artifacts,
        "ownership": classified_paths,
        "context_docs": context_docs,
        "prompt_injection_risks": prompt_injection_risks,
        "retained_history": retained_history,
        "dominant_language": _detect_language(language_sources),
        "recommended_validation": recommended_checks(root),
    }


def _section_text(text: str, heading: str) -> str:
    match = re.search(
        rf"^### {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^### |^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group("body").strip() if match else ""


def validate_plan_schema(
    text: str,
    declared_external_sources: bool = False,
    require_fidelity_passed: bool = False,
) -> list[str]:
    issues: list[str] = []
    if not re.search(r"(?mi)^(?:plan_schema_version|Plan Schema Version)\s*:\s*`?1`?\s*$", text):
        issues.append("missing or unsupported plan_schema_version")
    for section in REQUIRED_PLAN_SECTIONS:
        if not re.search(rf"(?m)^### {re.escape(section)}\s*$", text):
            issues.append(f"missing plan section: {section}")

    origin_body = _section_text(text, "Plan Origin")
    origin_lines = [line.strip().strip("`") for line in origin_body.splitlines() if line.strip()]
    origin_text = origin_lines[0] if origin_lines else ""
    if not origin_text:
        issues.append("Plan Origin is empty")
    elif origin_text not in PLAN_ORIGINS:
        issues.append(f"invalid Plan Origin: {origin_text}")

    traceability = _section_text(text, "Requirement Traceability")
    queue = _section_text(text, "Current Work Queue")
    requirement_ids = set(re.findall(r"\bREQ-\d{3}\b", traceability))
    if not requirement_ids:
        issues.append("Requirement Traceability has no stable requirement IDs")
    for requirement_id in sorted(requirement_ids):
        if requirement_id not in queue:
            issues.append(f"work queue does not cover {requirement_id}")

    sources = _section_text(text, "Inputs And Sources")
    if not sources:
        issues.append("Inputs And Sources is empty")
    if declared_external_sources and not re.search(r"https?://", sources):
        issues.append("declared external sources are missing from Inputs And Sources")

    decisions = _section_text(text, "User Decisions And Answers")
    if not decisions:
        issues.append("User Decisions And Answers is empty")

    fidelity = _section_text(text, "Plan Fidelity Check")
    if not fidelity:
        issues.append("Plan Fidelity Check is empty")
    elif require_fidelity_passed and re.search(r"(?m)^\s*-\s*\[ \]", fidelity):
        issues.append("Plan Fidelity Check has unchecked conditions")

    first_open = None
    for line in queue.splitlines():
        if re.search(r"(?:\[ \]|`(?:pending|in_progress|blocked)`)", line):
            match = re.search(r"\bWQ-\d{2}\b", line)
            if match:
                first_open = match.group(0)
                break
    resume = _section_text(text, "Resume Point")
    if first_open and first_open not in resume:
        issues.append(f"Resume Point does not identify first unfinished queue item {first_open}")
    if requirement_ids and len(queue.strip().splitlines()) < 1:
        issues.append("Current Work Queue is compressed or empty")
    return issues


def find_stale_completed_state(text: str) -> list[str]:
    stale = []
    patterns = {
        "next_work": r"\bnext work\b",
        "resume_instruction": r"\bresume (?:point|by|with|from)\b",
        "current_milestone": r"\bcurrent milestone\b",
        "active_blocker": r"\bactive blocker\b",
    }
    for match in re.finditer(
        r"(?ms)^## Recently Completed\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
    ):
        for line_number, line in enumerate(match.group("body").splitlines(), start=1):
            if "explicit follow-up" in line.lower() or "do not leave" in line.lower():
                continue
            for name, pattern in patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    stale.append(f"{name} in Recently Completed line {line_number}")
    return stale


def print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def find_placeholder_issues(text: str) -> list[str]:
    patterns = (r"\[TODO[:\]]", r"\{\{[^}]+\}\}")
    return [pattern for pattern in patterns if re.search(pattern, text)]
