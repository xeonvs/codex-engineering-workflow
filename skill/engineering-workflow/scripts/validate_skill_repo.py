#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


REQUIRED_PATHS = [
    "README.md",
    "LICENSE",
    "skill/engineering-workflow/SKILL.md",
    "skill/engineering-workflow/agents/openai.yaml",
    "skill/engineering-workflow/scripts/repo_audit.py",
    "skill/engineering-workflow/scripts/plan_bootstrap.py",
    "skill/engineering-workflow/scripts/validate_target_repo.py",
    "skill/engineering-workflow/scripts/sanitize_output.py",
    "skill/engineering-workflow/references/canonical_target.md",
    "skill/engineering-workflow/references/planning_and_backlog.md",
    "skill/engineering-workflow/assets/templates/AGENTS.md.tmpl",
]

PUBLIC_SCAN_PATHS = [
    "README.md",
    ".github/workflows/ci.yml",
    "skill/engineering-workflow",
]
PUBLIC_TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".tmpl", ".txt"}

FORBIDDEN_PATH_PARTS = {"__pycache__"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}
FORBIDDEN_TEXT_PATTERNS = {
    "absolute_home_path": re.compile(r"(^|[^A-Za-z0-9_])(/home/[A-Za-z0-9._-]+/)"),
    "windows_user_path": re.compile(r"[A-Za-z]:\\\\Users\\\\[A-Za-z0-9._ -]+\\\\"),
    "internal_hostname": re.compile(r"\b[a-zA-Z0-9.-]+\.(internal|corp|local)\b"),
    "credential_like_assignment": re.compile(
        r"\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[A-Za-z0-9._-]{8,}",
        re.IGNORECASE,
    ),
}

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def _extract_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(?P<body>.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    values: dict[str, str] = {}
    current_section = None
    for raw_line in match.group("body").splitlines():
        if not raw_line.strip():
            continue
        if not raw_line.startswith(" ") and ":" in raw_line:
            key, value = raw_line.split(":", 1)
            current_section = key.strip()
            if value.strip():
                values[current_section] = value.strip().strip("\"'")
            continue
        if current_section == "metadata" and raw_line.startswith("  ") and ":" in raw_line:
            key, value = raw_line.strip().split(":", 1)
            values[f"metadata.{key.strip()}"] = value.strip().strip("\"'")
    return values


def _iter_scan_files(repo_root: Path):
    for rel_path in PUBLIC_SCAN_PATHS:
        path = repo_root / rel_path
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix.lower() in PUBLIC_TEXT_SUFFIXES:
                yield path
            continue
        for child in path.rglob("*"):
            if child.is_file() and child.suffix.lower() in PUBLIC_TEXT_SUFFIXES:
                yield child


def _check_for_forbidden_paths(repo_root: Path) -> list[str]:
    candidate_paths: list[Path] = []
    git_dir = repo_root / ".git"
    if git_dir.exists():
        try:
            output = subprocess.run(
                ["git", "-C", str(repo_root), "ls-files", "--cached", "--others", "--exclude-standard"],
                check=True,
                capture_output=True,
                text=True,
            )
            candidate_paths = [repo_root / line for line in output.stdout.splitlines() if line.strip()]
        except subprocess.CalledProcessError:
            candidate_paths = []

    if not candidate_paths:
        candidate_paths = [path for path in repo_root.rglob("*") if path.is_file()]

    issues = []
    for path in candidate_paths:
        rel_path = path.relative_to(repo_root)
        if any(part in FORBIDDEN_PATH_PARTS for part in rel_path.parts):
            issues.append(f"Forbidden cache path present: {rel_path}")
            continue
        if path.suffix in FORBIDDEN_SUFFIXES:
            issues.append(f"Forbidden compiled artifact present: {rel_path}")
    return issues


def _scan_public_text(repo_root: Path) -> list[str]:
    issues = []
    for path in _iter_scan_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel_path = path.relative_to(repo_root)
        for name, pattern in FORBIDDEN_TEXT_PATTERNS.items():
            if pattern.search(text):
                issues.append(f"Forbidden {name} found in {rel_path}")
    return issues


def validate_skill_repo(repo_root: Path) -> dict:
    errors = []
    warnings = []
    skill_version = None

    for rel_path in REQUIRED_PATHS:
        if not (repo_root / rel_path).exists():
            errors.append(f"Missing required path: {rel_path}")

    skill_md = repo_root / "skill/engineering-workflow/SKILL.md"
    if skill_md.exists():
        text = skill_md.read_text(encoding="utf-8")
        frontmatter = _extract_frontmatter(text)
        if frontmatter.get("name") != "engineering-workflow" or not frontmatter.get("description"):
            errors.append("SKILL.md frontmatter is missing or malformed")
        version = frontmatter.get("metadata.version")
        if not version or not SEMVER_PATTERN.match(version):
            errors.append("SKILL.md metadata.version is missing or not SemVer")
        else:
            skill_version = version
        if "[TODO" in text or "TODO:" in text:
            errors.append("SKILL.md still contains TODO markers")

    readme = repo_root / "README.md"
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8")
        if "[TODO" in readme_text:
            errors.append("README.md still contains TODO markers")
        required_sections = [
            "## Quick Start",
            "## Installing The Skill",
            "## Using The Skill In Codex",
            "## Forced Skill Refresh Prompt",
            "## Operating Modes",
            "## Planning And Backlog Lifecycle",
            "## Example Workflows",
        ]
        for section in required_sections:
            if section not in readme_text:
                errors.append(f"README.md is missing required section: {section}")
        if 'CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"' not in readme_text:
            errors.append("README.md should explain the default CODEX_HOME location")
        if "## Versioning And Updates" not in readme_text:
            errors.append("README.md is missing versioning and update instructions")
        if skill_version and f"Current skill version: `{skill_version}`." not in readme_text:
            errors.append("README.md current skill version does not match SKILL.md metadata.version")

    openai_yaml = repo_root / "skill/engineering-workflow/agents/openai.yaml"
    if openai_yaml.exists():
        text = openai_yaml.read_text(encoding="utf-8")
        if "$engineering-workflow" not in text:
            errors.append("agents/openai.yaml default prompt does not mention $engineering-workflow")
        if "allow_implicit_invocation: false" not in text:
            warnings.append("agents/openai.yaml should keep allow_implicit_invocation: false")

    errors.extend(_check_for_forbidden_paths(repo_root))
    errors.extend(_scan_public_text(repo_root))

    return {"success": not errors, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate this public skill repository.")
    parser.add_argument("--repo-root", default=".", help="Path to the skill repository root")
    args = parser.parse_args()

    result = validate_skill_repo(Path(args.repo_root).resolve())
    print(result)
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
