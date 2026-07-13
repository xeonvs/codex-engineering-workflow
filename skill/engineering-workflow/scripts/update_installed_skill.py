#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


CANONICAL_UPSTREAM = "https://github.com/xeonvs/codex-engineering-workflow"
CANONICAL_SOURCE_PATH = "skill/engineering-workflow"
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
REQUIRED_CANDIDATE_PATHS = (
    "SKILL.md",
    "references",
    "scripts",
    "agents/openai.yaml",
)


class UpdateConflict(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _run_git(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise UpdateConflict("git_error", detail)
    return completed


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    values: dict[str, str] = {}
    section = ""
    for raw in text[4:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == 0 and raw.rstrip().endswith(":"):
            section = raw.rstrip()[:-1].strip()
            continue
        if ":" not in raw:
            continue
        key, value = raw.strip().split(":", 1)
        full_key = f"{section}.{key}" if indent and section else key
        values[full_key] = value.strip().strip("\"'")
    return values


def read_skill_identity(skill_dir: Path) -> dict[str, str]:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        raise UpdateConflict("missing_skill_file", "Candidate or installation is missing SKILL.md")
    metadata = _frontmatter(skill_file.read_text(encoding="utf-8"))
    name = metadata.get("name", "")
    version = metadata.get("metadata.version", "")
    if not name:
        raise UpdateConflict("invalid_frontmatter", "SKILL.md frontmatter is missing name")
    if not SEMVER_RE.fullmatch(version):
        raise UpdateConflict("invalid_version", "SKILL.md metadata.version is not valid SemVer")
    return {"name": name, "version": version}


def _semver_key(version: str) -> tuple[int, int, int, tuple[tuple[int, str], ...]]:
    match = SEMVER_RE.fullmatch(version)
    if not match:
        raise UpdateConflict("invalid_version", f"Invalid SemVer: {version}")
    prerelease = match.group(4)
    if prerelease is None:
        pre_key = ((2, ""),)
    else:
        parts = []
        for part in prerelease.split("."):
            parts.append((0, f"{int(part):020d}") if part.isdigit() else (1, part))
        pre_key = tuple(parts)
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), pre_key


def _normalized_repo(value: str) -> str:
    stripped = value.strip().rstrip("/")
    github_patterns = (
        re.compile(r"^https?://github\.com/(?P<path>[^/]+/[^/]+?)(?:\.git)?$", re.IGNORECASE),
        re.compile("^ssh" + r"://" + "git" + r"@github\.com/(?P<path>[^/]+/[^/]+?)(?:\.git)?$", re.IGNORECASE),
        re.compile("^git" + r"@github\.com:(?P<path>[^/]+/[^/]+?)(?:\.git)?$", re.IGNORECASE),
    )
    for pattern in github_patterns:
        match = pattern.fullmatch(stripped)
        if match:
            return "github.com/" + match.group("path").lower()
    if "://" not in stripped and not stripped.startswith("git@"):
        return str(Path(stripped).expanduser().resolve())
    return stripped.removesuffix(".git")


def _public_source_label(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return "invalid-source-url"
    if parsed.scheme.lower() not in {"http", "https"} or parsed.username is None:
        return value
    host = parsed.hostname or "redacted-source"
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port is not None:
        host = f"{host}:{port}"
    return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))


def _reject_source_credentials(value: str) -> None:
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise UpdateConflict("invalid_source_url", "Source repository URL is malformed") from exc
    if parsed.scheme.lower() in {"http", "https"} and parsed.username is not None:
        raise UpdateConflict("source_credentials_refused", "Source repository URL must not contain embedded credentials")


def is_canonical_upstream(source_repo: str) -> bool:
    return _normalized_repo(source_repo) == _normalized_repo(CANONICAL_UPSTREAM)


def _safe_source_path(value: str) -> Path:
    path = Path(value.replace("\\", "/"))
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise UpdateConflict("unsafe_source_path", "source path must be a normalized relative path")
    return path


def _validate_symlinks(candidate: Path) -> None:
    root = candidate.resolve()
    for path in candidate.rglob("*"):
        if not path.is_symlink():
            continue
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise UpdateConflict("invalid_candidate_symlink", "Candidate contains a broken symlink") from exc
        if not resolved.is_relative_to(root):
            raise UpdateConflict("escaping_candidate_symlink", "Candidate contains a symlink outside its tree")


def validate_candidate(candidate: Path) -> dict[str, Any]:
    if not candidate.is_dir():
        raise UpdateConflict("missing_source_path", "Source path is not a directory in the selected ref")
    for relative in REQUIRED_CANDIDATE_PATHS:
        if not (candidate / relative).exists():
            raise UpdateConflict("invalid_candidate", f"Candidate is missing required path: {relative}")
    identity = read_skill_identity(candidate)
    if identity["name"] != "engineering-workflow":
        raise UpdateConflict("wrong_skill_name", "Candidate SKILL.md has the wrong skill name")
    _validate_symlinks(candidate)
    return {"success": True, "name": identity["name"], "version": identity["version"]}


def _materialize_tree(checkout: Path, resolved: str, source_path: str, candidate: Path) -> None:
    safe_source = _safe_source_path(source_path).as_posix()
    object_type = _run_git("cat-file", "-t", f"{resolved}:{safe_source}", cwd=checkout).stdout.strip()
    if object_type != "tree":
        raise UpdateConflict("invalid_source_path", "Source path is not a directory tree in the selected ref")
    completed = subprocess.run(
        ["git", "ls-tree", "-rz", "-r", resolved, "--", safe_source],
        cwd=checkout,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise UpdateConflict("git_error", "Unable to inspect candidate tree")
    candidate.mkdir(parents=True)
    prefix = safe_source.rstrip("/") + "/"
    for record in completed.stdout.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_kind, object_id = metadata.decode("ascii").split()
            repo_path = raw_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise UpdateConflict("invalid_candidate_path", "Candidate contains an unsupported path") from exc
        if not repo_path.startswith(prefix):
            raise UpdateConflict("invalid_candidate_path", "Candidate tree entry escapes the source path")
        relative = Path(repo_path[len(prefix) :])
        if not relative.parts or relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise UpdateConflict("invalid_candidate_path", "Candidate contains an unsafe path")
        destination = candidate / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if object_kind != "blob":
            raise UpdateConflict("invalid_candidate_object", "Candidate contains a non-file object")
        blob = subprocess.run(
            ["git", "cat-file", "blob", object_id],
            cwd=checkout,
            capture_output=True,
            check=False,
        )
        if blob.returncode != 0:
            raise UpdateConflict("git_error", "Unable to read a candidate object")
        if mode == "120000":
            try:
                link_target = blob.stdout.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise UpdateConflict("invalid_candidate_symlink", "Candidate symlink target is not UTF-8") from exc
            os.symlink(link_target, destination)
        elif mode in {"100644", "100755"}:
            destination.write_bytes(blob.stdout)
            destination.chmod(0o755 if mode == "100755" else 0o644)
        else:
            raise UpdateConflict("invalid_candidate_mode", "Candidate contains an unsupported file mode")


def _clone_candidate(source_repo: str, source_path: str, ref: str, temp_root: Path) -> tuple[Path, Path, str]:
    checkout = temp_root / "source"
    _run_git("clone", "--quiet", "--no-checkout", "--", source_repo, str(checkout))
    resolved = _run_git("rev-parse", f"{ref}^{{commit}}", cwd=checkout).stdout.strip()
    candidate = temp_root / "candidate"
    _materialize_tree(checkout, resolved, source_path, candidate)
    return checkout, candidate, resolved


def _git_root(path: Path) -> Path | None:
    result = _run_git("-C", str(path), "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def _installation_details(install_path: Path, source_path: str) -> dict[str, Any]:
    if not install_path.exists() and not install_path.is_symlink():
        raise UpdateConflict("missing_installation", "The exact install path does not exist")
    symlinked = install_path.is_symlink()
    try:
        resolved = install_path.resolve(strict=True)
    except OSError as exc:
        raise UpdateConflict("broken_installation_symlink", "The install path cannot be resolved") from exc
    if not resolved.is_dir():
        raise UpdateConflict("invalid_installation", "The install path does not resolve to a directory")
    identity = read_skill_identity(resolved)
    if identity["name"] != "engineering-workflow":
        raise UpdateConflict("wrong_installed_skill", "The exact install path is not engineering-workflow")
    root = _git_root(resolved)
    expected_relative = _safe_source_path(source_path)
    is_source_checkout = bool(root and (root / expected_relative).resolve() == resolved)
    if root and root == resolved:
        is_source_checkout = True
    strategy = "git_checkout" if is_source_checkout else "copied"
    installation_type = "symlink" if symlinked else strategy
    return {
        "active_installation_path": str(install_path.absolute()),
        "resolved_target_path": str(resolved),
        "installation_type": installation_type,
        "update_strategy": strategy,
        "git_root": root,
        "previous_version": identity["version"],
    }


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _tree_entries(root: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries[relative] = "symlink:" + os.readlink(path)
        elif path.is_file():
            entries[relative] = "file:" + _file_digest(path)
    return entries


def diff_summary(current: Path, candidate: Path) -> dict[str, Any]:
    old_files = _tree_entries(current)
    new_files = _tree_entries(candidate)
    old_names = set(old_files)
    new_names = set(new_files)
    modified = sorted(name for name in old_names & new_names if old_files[name] != new_files[name])
    return {
        "added": sorted(new_names - old_names),
        "modified": modified,
        "deleted": sorted(old_names - new_names),
        "counts": {
            "added": len(new_names - old_names),
            "modified": len(modified),
            "deleted": len(old_names - new_names),
        },
    }


def _checkout_state(
    details: dict[str, Any],
    source_repo: str,
    ref: str,
    candidate_checkout: Path,
    candidate_commit: str,
) -> dict[str, Any]:
    root = details["git_root"]
    assert isinstance(root, Path)
    dirty = _run_git("status", "--porcelain", cwd=root).stdout.strip()
    if dirty:
        raise UpdateConflict("dirty_checkout", "Git checkout has local changes")
    remote_result = _run_git("remote", "get-url", "origin", cwd=root, check=False)
    if remote_result.returncode != 0:
        raise UpdateConflict("missing_origin", "Git checkout has no origin remote")
    actual_remote = remote_result.stdout.strip()
    if _normalized_repo(actual_remote) != _normalized_repo(source_repo):
        raise UpdateConflict("remote_mismatch", "Git checkout origin does not match source repository")
    branch_result = _run_git("symbolic-ref", "--quiet", "--short", "HEAD", cwd=root, check=False)
    if branch_result.returncode != 0:
        raise UpdateConflict("detached_checkout", "Git checkout is detached")
    branch = branch_result.stdout.strip()
    if re.fullmatch(r"[A-Za-z0-9._/-]+", ref) and ref not in {"HEAD", branch, f"refs/heads/{branch}"}:
        raise UpdateConflict("branch_ref_mismatch", "Current branch does not match the requested ref")
    current_commit = _run_git("rev-parse", "HEAD", cwd=root).stdout.strip()
    candidate_has_current = _run_git("cat-file", "-e", f"{current_commit}^{{commit}}", cwd=candidate_checkout, check=False)
    if candidate_has_current.returncode != 0:
        raise UpdateConflict("divergent_checkout", "Current checkout commit is absent from source history")
    ancestor = _run_git("merge-base", "--is-ancestor", current_commit, candidate_commit, cwd=candidate_checkout, check=False)
    if ancestor.returncode != 0:
        raise UpdateConflict("divergent_checkout", "Git checkout cannot be updated by fast-forward")
    return {"branch": branch, "current_commit": current_commit, "remote": actual_remote}


def _backup_destination(backup_dir: Path, version: str) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"engineering-workflow-{version}-{stamp}"
    if destination.exists():
        destination = backup_dir / f"engineering-workflow-{version}-{stamp}-{uuid.uuid4().hex[:8]}"
    return destination


def _replace_copied_installation(current: Path, candidate: Path, backup_dir: Path, version: str) -> Path:
    resolved_current = current.resolve()
    resolved_backup_dir = backup_dir.resolve()
    if resolved_backup_dir == resolved_current or resolved_backup_dir.is_relative_to(resolved_current):
        raise UpdateConflict("unsafe_backup_path", "Backup directory must be outside the installed skill tree")
    backup = _backup_destination(backup_dir, version)
    shutil.copytree(current, backup, symlinks=True)
    stage_parent = Path(tempfile.mkdtemp(prefix=".engineering-workflow-stage-", dir=current.parent))
    staged = stage_parent / current.name
    rollback = current.parent / f".{current.name}.rollback-{uuid.uuid4().hex}"
    try:
        shutil.copytree(candidate, staged, symlinks=True)
        os.replace(current, rollback)
        try:
            os.replace(staged, current)
        except Exception:
            os.replace(rollback, current)
            raise
        shutil.rmtree(rollback)
    except Exception as exc:
        if rollback.exists() and not current.exists():
            os.replace(rollback, current)
        raise UpdateConflict("replacement_failed", "Copied installation replacement failed and was rolled back") from exc
    finally:
        shutil.rmtree(stage_parent, ignore_errors=True)
        if rollback.exists():
            shutil.rmtree(rollback, ignore_errors=True)
    return backup


def update_installation(
    install_path: Path,
    source_repo: str = CANONICAL_UPSTREAM,
    source_path: str = CANONICAL_SOURCE_PATH,
    ref: str = "main",
    *,
    apply: bool = False,
    allow_downgrade: bool = False,
    backup_dir: Path | None = None,
    confirm_alternate_upstream: bool = False,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "success": False,
        "mode": "apply" if apply else "check",
        "source_repository": _public_source_label(source_repo),
        "source_path": source_path,
        "source_ref": ref,
        "resolved_commit": None,
        "previous_version": None,
        "candidate_version": None,
        "active_installation_path": str(install_path.absolute()),
        "resolved_target_path": None,
        "installation_type": None,
        "backup_path": None,
        "validation_result": {"success": False},
        "update_status": "failed",
        "restart_or_next_turn_required": False,
        "errors": [],
    }
    try:
        _reject_source_credentials(source_repo)
        details = _installation_details(install_path, source_path)
        result.update({key: value for key, value in details.items() if key not in {"git_root", "update_strategy"}})
        with tempfile.TemporaryDirectory(prefix="engineering-workflow-update-") as temp_name:
            checkout, candidate, resolved_commit = _clone_candidate(source_repo, source_path, ref, Path(temp_name))
            validation = validate_candidate(candidate)
            result["resolved_commit"] = resolved_commit
            result["candidate_version"] = validation["version"]
            result["validation_result"] = validation
            current = Path(str(result["resolved_target_path"]))
            result["diff_summary"] = diff_summary(current, candidate)

            if _semver_key(validation["version"]) < _semver_key(str(result["previous_version"])) and not allow_downgrade:
                raise UpdateConflict("downgrade_refused", "Candidate version is older; use --allow-downgrade to proceed")
            if apply and not is_canonical_upstream(source_repo) and not confirm_alternate_upstream:
                result["update_status"] = "confirmation_required"
                raise UpdateConflict("alternate_upstream_confirmation_required", "Alternate upstream requires explicit confirmation")

            if details["update_strategy"] == "git_checkout":
                state = _checkout_state(details, source_repo, ref, checkout, resolved_commit)
                result["checkout"] = {"branch": state["branch"], "current_commit": state["current_commit"]}
                if state["current_commit"] == resolved_commit:
                    result["success"] = True
                    result["update_status"] = "up_to_date"
                    return result
                if apply:
                    root = details["git_root"]
                    assert isinstance(root, Path)
                    _run_git("fetch", "--quiet", "--", source_repo, ref, cwd=root)
                    fetched = _run_git("rev-parse", "FETCH_HEAD", cwd=root).stdout.strip()
                    if fetched != resolved_commit:
                        raise UpdateConflict("source_changed", "Source ref changed between inspection and apply")
                    _run_git("-c", "core.hooksPath=/dev/null", "merge", "--ff-only", "FETCH_HEAD", cwd=root)
            elif apply:
                selected_backup = backup_dir or current.parent / ".engineering-workflow-backups"
                backup = _replace_copied_installation(
                    current,
                    candidate,
                    selected_backup.expanduser().resolve(),
                    str(result["previous_version"]),
                )
                result["backup_path"] = str(backup)

            result["success"] = True
            result["update_status"] = "updated" if apply else "update_available"
            result["restart_or_next_turn_required"] = bool(apply)
            return result
    except UpdateConflict as exc:
        if result["update_status"] != "confirmation_required":
            result["update_status"] = exc.code
        result["errors"].append({"code": exc.code, "message": str(exc)})
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or safely update the exact active engineering-workflow installation.")
    parser.add_argument("--install-path", required=True)
    parser.add_argument("--source-repo", default=CANONICAL_UPSTREAM)
    parser.add_argument("--source-path", default=CANONICAL_SOURCE_PATH)
    parser.add_argument("--ref", default="main")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-downgrade", action="store_true")
    parser.add_argument("--backup-dir")
    parser.add_argument("--confirm-alternate-upstream", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()

    result = update_installation(
        Path(args.install_path).expanduser(),
        args.source_repo,
        args.source_path,
        args.ref,
        apply=args.apply,
        allow_downgrade=args.allow_downgrade,
        backup_dir=Path(args.backup_dir) if args.backup_dir else None,
        confirm_alternate_upstream=args.confirm_alternate_upstream,
    )
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result['update_status']}: {result.get('previous_version')} -> {result.get('candidate_version')}")
        for error in result["errors"]:
            print(f"{error['code']}: {error['message']}")
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
