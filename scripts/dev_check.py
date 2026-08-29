#!/usr/bin/env python3
"""Run repository-maintainer checks with private logs and bounded output."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]
RUFF_VERSION = "0.16.4"
PYTHON_TARGETS = ("scripts", "skill/engineering-workflow/scripts", "tests")
PROFILE_NAMES = (
    "focused",
    "format",
    "lint",
    "quality",
    "contracts",
    "tests",
    "package",
    "security",
    "full",
    "release",
)


class Check(NamedTuple):
    name: str
    command: tuple[str, ...]
    expected_text: str | None = None


class CheckResult(NamedTuple):
    name: str
    status: str
    returncode: int
    duration_seconds: float
    log_path: Path


def _python(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


def _quality_checks(*, fix: bool = False) -> list[Check]:
    ruff = _python("-m", "ruff")
    checks = [Check("ruff-version", (*ruff, "--version"), f"ruff {RUFF_VERSION}")]
    if fix:
        checks.extend(
            [
                Check("ruff-lint-fix", (*ruff, "check", "--no-cache", "--fix", *PYTHON_TARGETS)),
                Check("ruff-format-fix", (*ruff, "format", "--no-cache", *PYTHON_TARGETS)),
            ]
        )
    else:
        checks.extend(
            [
                Check("ruff-format", (*ruff, "format", "--no-cache", "--check", *PYTHON_TARGETS)),
                Check("ruff-lint", (*ruff, "check", "--no-cache", *PYTHON_TARGETS)),
            ]
        )
    return checks


def _validator(name: str) -> Check:
    return Check(
        name,
        _python("skill/engineering-workflow/scripts/validate_skill_repo.py", "--repo-root", "."),
    )


def _contract_checks() -> list[Check]:
    patterns = (
        "test_instruction_contract.py",
        "test_plan_lifecycle.py",
        "test_skill_repo_validation.py",
        "test_upgrade_target_workflow.py",
        "test_validation.py",
    )
    return [_validator("validate-contracts")] + [
        Check(
            f"contract-{Path(pattern).stem.removeprefix('test_')}",
            _python("-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"),
        )
        for pattern in patterns
    ]


def _security_checks(log_dir: Path) -> list[Check]:
    return [
        Check(
            "public-tree-privacy",
            _python(
                "skill/engineering-workflow/scripts/sanitize_output.py",
                "--public-tree",
                "--repo-root",
                ".",
            ),
        ),
        Check(
            "gitleaks-tree",
            (
                "gitleaks",
                "dir",
                ".",
                "--redact=100",
                "--report-format=json",
                f"--report-path={log_dir / 'gitleaks-tree.json'}",
            ),
        ),
        Check(
            "gitleaks-history",
            (
                "gitleaks",
                "git",
                ".",
                "--redact=100",
                "--log-opts=--all",
                "--report-format=json",
                f"--report-path={log_dir / 'gitleaks-history.json'}",
            ),
        ),
    ]


def select_checks(profile: str, *, log_dir: Path, test_pattern: str | None, fix: bool) -> list[Check]:
    if profile == "focused":
        if not test_pattern:
            raise ValueError("focused requires --test-pattern")
        if Path(test_pattern).name != test_pattern or re.fullmatch(r"test_[A-Za-z0-9_]+\.py", test_pattern) is None:
            raise ValueError("--test-pattern must be one test_*.py basename")
        return [
            Check(
                "focused-tests",
                _python("-m", "unittest", "discover", "-s", "tests", "-p", test_pattern, "-v"),
            )
        ]
    if fix and profile != "format":
        raise ValueError("--fix is allowed only with the format profile")
    if profile == "format":
        return _quality_checks(fix=fix)
    if profile == "lint":
        quality = _quality_checks()
        return [quality[0], quality[2]]
    if profile == "quality":
        return _quality_checks()
    if profile == "contracts":
        return _contract_checks()
    if profile == "tests":
        return [Check("all-tests", _python("-m", "unittest", "discover", "-s", "tests", "-v"))]
    if profile == "package":
        return [Check("marketplace-package", _python("scripts/build_marketplace_package.py", "--check"))]
    if profile == "security":
        return _security_checks(log_dir)
    if profile == "full":
        return [
            *_quality_checks(),
            _validator("validate-before-tests"),
            Check("all-tests", _python("-m", "unittest", "discover", "-s", "tests", "-v")),
            _validator("validate-after-tests"),
            Check("marketplace-package", _python("scripts/build_marketplace_package.py", "--check")),
            Check("patch-whitespace", ("git", "diff", "--check")),
            Check("head-whitespace", ("git", "show", "--check", "--format=", "HEAD")),
        ]
    if profile == "release":
        return [
            *select_checks("full", log_dir=log_dir, test_pattern=None, fix=False),
            *_security_checks(log_dir),
        ]
    raise ValueError(f"unknown profile: {profile}")


def child_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUNBUFFERED"] = "1"
    return environment


def _run_check(check: Check, *, log_dir: Path) -> CheckResult:
    log_path = log_dir / f"{check.name}.log"
    started = time.monotonic()
    try:
        with log_path.open("w", encoding="utf-8") as stream:
            log_path.chmod(0o600)
            completed = subprocess.run(
                check.command,
                cwd=REPO_ROOT,
                env=child_environment(),
                stdout=stream,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
        returncode = completed.returncode
        if returncode == 0 and check.expected_text is not None:
            if check.expected_text != log_path.read_text(encoding="utf-8", errors="replace").strip():
                returncode = 1
    except FileNotFoundError:
        log_path.write_text(f"required executable not found: {check.command[0]}\n", encoding="utf-8")
        log_path.chmod(0o600)
        returncode = 127
    duration = time.monotonic() - started
    return CheckResult(check.name, "PASS" if returncode == 0 else "FAIL", returncode, duration, log_path)


def run_checks(checks: list[Check], *, log_dir: Path, keep_going: bool) -> list[CheckResult]:
    results: list[CheckResult] = []
    for check in checks:
        result = _run_check(check, log_dir=log_dir)
        results.append(result)
        if result.returncode != 0 and not keep_going:
            break
    return results


def _print_failure_tail(result: CheckResult, line_count: int) -> None:
    if result.returncode == 0 or line_count <= 0:
        return
    lines = result.log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    print(f"--- bounded tail: {result.name} ({min(line_count, len(lines))} lines) ---")
    for line in lines[-line_count:]:
        print(line)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=PROFILE_NAMES)
    parser.add_argument("--test-pattern", help="Basename test_*.py for the focused profile")
    parser.add_argument("--fix", action="store_true", help="Apply Ruff fixes; valid only for the format profile")
    parser.add_argument("--keep-going", action="store_true", help="Run remaining checks after a failure")
    parser.add_argument(
        "--keep-logs", action="store_true", help="Retain successful logs in the private temporary directory"
    )
    parser.add_argument(
        "--show-failure-tail",
        type=int,
        default=0,
        choices=range(0, 101),
        metavar="0..100",
        help="Explicitly print up to 100 raw failure lines; default prints none",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log_dir = Path(tempfile.mkdtemp(prefix="engineering-workflow-check-"))
    log_dir.chmod(0o700)
    try:
        checks = select_checks(
            args.profile,
            log_dir=log_dir,
            test_pattern=args.test_pattern,
            fix=args.fix,
        )
    except ValueError as error:
        shutil.rmtree(log_dir)
        print(f"configuration error: {error}", file=sys.stderr)
        return 2

    results = run_checks(checks, log_dir=log_dir, keep_going=args.keep_going)
    failed = [result for result in results if result.returncode != 0]
    for result in results:
        print(f"{result.status:4} {result.name} ({result.duration_seconds:.2f}s)")
        _print_failure_tail(result, args.show_failure_tail)

    logs_retained = bool(failed or args.keep_logs)
    if logs_retained:
        print(f"private logs: {log_dir}")
    else:
        shutil.rmtree(log_dir)
    print(f"summary: {len(results) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
