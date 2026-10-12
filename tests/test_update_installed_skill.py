from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_support import load_script_module


updater = load_script_module("update_installed_skill")
SOURCE_PATH = Path("skill/engineering-workflow")


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def write_candidate(repo: Path, version: str, name: str = "engineering-workflow") -> Path:
    skill = repo / SOURCE_PATH
    (skill / "references").mkdir(parents=True, exist_ok=True)
    (skill / "scripts").mkdir(parents=True, exist_ok=True)
    (skill / "agents").mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Offline updater fixture.\nmetadata:\n  version: {version}\n---\n\n# Fixture\n",
        encoding="utf-8",
    )
    (skill / "references" / "policy.md").write_text("policy\n", encoding="utf-8")
    (skill / "scripts" / "tool.py").write_text("VALUE = 1\n", encoding="utf-8")
    (skill / "agents" / "openai.yaml").write_text("interface:\n  display_name: Fixture\n", encoding="utf-8")
    if updater._semver_key(version) >= updater._semver_key("0.10.0"):
        (skill / "assets").mkdir(parents=True, exist_ok=True)
        local_descriptor = Path(updater.__file__).resolve().parents[1] / "assets" / "release_adoption.json"
        descriptor = json.loads(local_descriptor.read_text())
        descriptor["skill_version"] = version
        (skill / "assets" / "release_adoption.json").write_text(json.dumps(descriptor))
        (skill / "references" / "documentation_navigation.md").write_text("Fixture navigation contract\n")
        for name in ("documentation_navigation", "documentation_restructure", "release_adoption", "workflow_updates"):
            (skill / "scripts" / f"{name}.py").write_text("# Inert fixture; never executed\n")
    return skill


def init_upstream(root: Path, version: str = "0.4.1") -> Path:
    repo = root / "upstream"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", ('fixture' '@example.test'))
    write_candidate(repo, version)
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", f"version {version}")
    return repo


def commit_version(repo: Path, version: str) -> str:
    path = repo / SOURCE_PATH / "SKILL.md"
    text = re.sub(r"(?m)^  version: .+$", f"  version: {version}", path.read_text(encoding="utf-8"))
    path.write_text(text, encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", f"version {version}")
    return git(repo, "rev-parse", "HEAD")


class UpdateInstalledSkillTests(unittest.TestCase):
    def test_plugin_managed_offline_check_reports_unknown_without_cache_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugin = root / "cache" / "engineering-workflow"
            install = plugin / "skills" / "engineering-workflow"
            write_candidate(root / "source", "0.8.0")
            shutil.copytree(root / "source" / SOURCE_PATH, install)
            (plugin / ".codex-plugin").mkdir(parents=True)
            (plugin / ".claude-plugin").mkdir(parents=True)
            (plugin / ".codex-plugin" / "plugin.json").write_text("{}\n", encoding="utf-8")
            (plugin / ".claude-plugin" / "plugin.json").write_text("{}\n", encoding="utf-8")
            before = {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()}

            with mock.patch.object(updater, "_clone_candidate", side_effect=updater.UpdateConflict(
                "upstream_unavailable", "Upstream could not be checked; currentness is unknown"
            )):
                result = updater.update_installation(install)

            after = {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()}
            self.assertFalse(result["success"], result)
            self.assertEqual(result["installation_type"], "plugin_managed")
            self.assertEqual(result["update_status"], "upstream_unavailable")
            self.assertEqual(result["currentness"], "unknown")
            self.assertEqual(result["next_agent_action"], "continue_with_installed_skill")
            self.assertIsInstance(result["plugin_root"], str)
            json.dumps(result)
            self.assertEqual(before, after)

    def test_check_mode_reports_candidate_without_mutating_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")
            result = updater.update_installation(install, str(source), str(SOURCE_PATH), "main")
            self.assertTrue(result["success"], result)
            self.assertEqual(result["update_status"], "update_available")
            self.assertEqual(result["previous_version"], "0.4.1")
            self.assertEqual(result["candidate_version"], "0.5.0")
            self.assertTrue(result["instructions_changed"])
            self.assertEqual(result["version_change_kind"], "minor")
            self.assertTrue(result["major_or_minor_version_changed"])
            self.assertEqual(result["recommended_action"], "update_installed_skill")
            self.assertTrue(result["confirmation_required"])
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")

    def test_no_content_drift_routes_to_refresh_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root, "0.5.0")
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)

            result = updater.update_installation(install, str(source), str(SOURCE_PATH), "main")

            self.assertTrue(result["success"], result)
            self.assertEqual(result["update_status"], "up_to_date")
            self.assertFalse(result["skill_content_changed"])
            self.assertFalse(result["instructions_changed"])
            self.assertEqual(result["version_change_kind"], "none")
            self.assertEqual(result["recommended_action"], "refresh_loaded_skill")
            self.assertEqual(result["next_agent_action"], "refresh_loaded_skill")

    def test_semver_and_instruction_drift_drive_agent_routing(self):
        summary = {
            "added": [],
            "modified": ["SKILL.md", "references/policy.md"],
            "deleted": [],
            "counts": {"added": 0, "modified": 2, "deleted": 0},
        }
        cases = (
            ("0.5.0", "1.0.0", "major", True),
            ("0.5.0", "0.6.0", "minor", True),
            ("0.5.0", "0.5.1", "patch", False),
            ("1.0.0", "0.5.0", "downgrade", True),
        )
        for previous, candidate, kind, major_or_minor in cases:
            with self.subTest(candidate=candidate):
                decision = updater.refresh_decision(
                    previous,
                    candidate,
                    summary,
                    canonical_upstream=True,
                )
                self.assertTrue(decision["instructions_changed"])
                self.assertEqual(decision["version_change_kind"], kind)
                self.assertEqual(decision["major_or_minor_version_changed"], major_or_minor)
                self.assertEqual(decision["recommended_action"], "update_installed_skill")
                self.assertEqual(decision["automatic_update_allowed"], kind != "downgrade")
                self.assertFalse(decision["confirmation_required"])

    def test_non_instruction_skill_content_still_routes_to_update(self):
        summary = {
            "added": [],
            "modified": ["scripts/tool.py"],
            "deleted": [],
            "counts": {"added": 0, "modified": 1, "deleted": 0},
        }
        decision = updater.refresh_decision("0.5.0", "0.5.0", summary, canonical_upstream=True)
        self.assertTrue(decision["skill_content_changed"])
        self.assertFalse(decision["instructions_changed"])
        self.assertEqual(decision["recommended_action"], "update_installed_skill")
        self.assertTrue(decision["automatic_update_allowed"])

    def test_copied_install_apply_creates_backup_and_replaces_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            backup_root = root / "backups"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")
            expected = git(source, "rev-parse", "HEAD")
            result = updater.update_installation(
                install,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                backup_dir=backup_root,
                confirm_alternate_upstream=True,
                expected_commit=expected,
            )
            self.assertTrue(result["success"], result)
            self.assertEqual(result["installation_type"], "copied")
            self.assertEqual(result["update_status"], "updated")
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.5.0")
            backup = Path(result["backup_path"])
            self.assertTrue(backup.is_dir())
            self.assertEqual(updater.read_skill_identity(backup)["version"], "0.4.1")

    def test_canonical_copy_update_needs_no_alternate_source_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")

            with mock.patch.object(updater, "is_canonical_upstream", return_value=True):
                result = updater.update_installation(
                    install,
                    str(source),
                    str(SOURCE_PATH),
                    "main",
                    apply=True,
                    backup_dir=root / "backups",
                )

            self.assertTrue(result["success"], result)
            self.assertTrue(result["automatic_update_allowed"])
            self.assertFalse(result["confirmation_required"])
            self.assertEqual(result["update_status"], "updated")
            self.assertEqual(result["next_agent_action"], "refresh_loaded_skill")

    def test_symlink_install_preserves_link_and_updates_resolved_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            target = root / "target"
            link = root / "active-skill"
            shutil.copytree(source / SOURCE_PATH, target)
            link.symlink_to(target, target_is_directory=True)
            commit_version(source, "0.5.0")
            expected = git(source, "rev-parse", "HEAD")
            result = updater.update_installation(
                link,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                backup_dir=root / "backups",
                confirm_alternate_upstream=True,
                expected_commit=expected,
            )
            self.assertTrue(result["success"], result)
            self.assertEqual(result["installation_type"], "symlink")
            self.assertTrue(link.is_symlink())
            self.assertEqual(updater.read_skill_identity(target)["version"], "0.5.0")

    def test_git_checkout_fast_forwards_without_merge_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            checkout = root / "checkout"
            subprocess.run(["git", "clone", "-q", str(source), str(checkout)], check=True)
            expected = commit_version(source, "0.5.0")
            result = updater.update_installation(
                checkout / SOURCE_PATH,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                confirm_alternate_upstream=True,
                expected_commit=expected,
            )
            self.assertTrue(result["success"], result)
            self.assertEqual(result["installation_type"], "git_checkout")
            self.assertEqual(git(checkout, "rev-parse", "HEAD"), expected)
            self.assertEqual(git(checkout, "rev-list", "--count", "HEAD"), "2")

    def test_dirty_checkout_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            checkout = root / "checkout"
            subprocess.run(["git", "clone", "-q", str(source), str(checkout)], check=True)
            commit_version(source, "0.5.0")
            expected = git(source, "rev-parse", "HEAD")
            (checkout / SOURCE_PATH / "references" / "policy.md").write_text("local edit\n", encoding="utf-8")
            result = updater.update_installation(
                checkout / SOURCE_PATH,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                confirm_alternate_upstream=True,
                expected_commit=expected,
            )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "dirty_checkout")

    def test_divergent_checkout_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            checkout = root / "checkout"
            subprocess.run(["git", "clone", "-q", str(source), str(checkout)], check=True)
            git(checkout, "config", "user.name", "Fixture")
            git(checkout, "config", "user.email", ('fixture' '@example.test'))
            commit_version(source, "0.5.0")
            expected = git(source, "rev-parse", "HEAD")
            (checkout / "LOCAL.md").write_text("local commit\n", encoding="utf-8")
            git(checkout, "add", ".")
            git(checkout, "commit", "-q", "-m", "local divergence")
            result = updater.update_installation(
                checkout / SOURCE_PATH,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                confirm_alternate_upstream=True,
                expected_commit=expected,
            )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "divergent_checkout")

    def test_downgrade_requires_explicit_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root, "0.5.0")
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            path = install / "SKILL.md"
            path.write_text(path.read_text(encoding="utf-8").replace("0.5.0", "0.6.0"), encoding="utf-8")
            refused = updater.update_installation(install, str(source), str(SOURCE_PATH), "main")
            self.assertFalse(refused["success"])
            self.assertEqual(refused["update_status"], "downgrade_refused")
            allowed = updater.update_installation(
                install,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                allow_downgrade=True,
                backup_dir=root / "backups",
                confirm_alternate_upstream=True,
                expected_commit=git(source, "rev-parse", "HEAD"),
            )
            self.assertTrue(allowed["success"], allowed)
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.5.0")

    def test_invalid_candidates_are_rejected_structurally(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing"
            missing.mkdir()
            with self.assertRaises(updater.UpdateConflict) as missing_error:
                updater.validate_candidate(missing)
            self.assertEqual(missing_error.exception.code, "invalid_candidate")

            wrong = root / "wrong"
            repo = root / "repo"
            repo.mkdir()
            candidate = write_candidate(repo, "0.5.0", name="other-skill")
            shutil.copytree(candidate, wrong)
            with self.assertRaises(updater.UpdateConflict) as wrong_error:
                updater.validate_candidate(wrong)
            self.assertEqual(wrong_error.exception.code, "wrong_skill_name")

            no_skill = root / "no-skill"
            (no_skill / "references").mkdir(parents=True)
            (no_skill / "scripts").mkdir()
            (no_skill / "agents").mkdir()
            (no_skill / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
            with self.assertRaises(updater.UpdateConflict) as no_skill_error:
                updater.validate_candidate(no_skill)
            self.assertEqual(no_skill_error.exception.code, "invalid_candidate")

    def test_candidate_symlink_cannot_escape_candidate_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            candidate = write_candidate(repo, "0.5.0")
            outside = root / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            (candidate / "references" / "outside-link.txt").symlink_to(outside)
            with self.assertRaises(updater.UpdateConflict) as error:
                updater.validate_candidate(candidate)
            self.assertEqual(error.exception.code, "escaping_candidate_symlink")

    def test_candidate_identity_is_not_read_before_symlink_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            outside = root / "outside-skill.md"
            candidate.mkdir()
            outside.write_text("outside\n", encoding="utf-8")
            (candidate / "SKILL.md").symlink_to(outside)

            with mock.patch.object(
                updater,
                "read_skill_identity",
                side_effect=AssertionError("identity reader must not follow an escaping link"),
            ):
                with self.assertRaises(updater.UpdateConflict) as error:
                    updater.validate_candidate(candidate)

            self.assertEqual(error.exception.code, "escaping_candidate_symlink")

    def test_candidate_skill_file_must_be_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            (candidate / "references").mkdir(parents=True)
            (candidate / "scripts").mkdir()
            (candidate / "agents").mkdir()
            (candidate / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
            (candidate / "SKILL.md").write_bytes(b"\xff\xfe")

            with self.assertRaises(updater.UpdateConflict) as error:
                updater.validate_candidate(candidate)

            self.assertEqual(error.exception.code, "invalid_skill_file")

    def test_alternate_upstream_requires_confirmation_for_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")
            result = updater.update_installation(
                install,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
            )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "confirmation_required")
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")

    def test_alternate_apply_requires_reviewed_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")

            result = updater.update_installation(
                install,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                confirm_alternate_upstream=True,
            )

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "expected_commit_required")
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")

    def test_alternate_apply_rejects_ref_move_after_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            reviewed = commit_version(source, "0.5.0")
            checked = updater.update_installation(install, str(source), str(SOURCE_PATH), "main")
            self.assertEqual(checked["resolved_commit"], reviewed)
            commit_version(source, "0.5.1")

            result = updater.update_installation(
                install,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                confirm_alternate_upstream=True,
                expected_commit=reviewed,
            )

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "expected_commit_mismatch")
            self.assertEqual(result["expected_commit"], reviewed)
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")

    def test_malformed_expected_commit_is_refused_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")

            result = updater.update_installation(
                install,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                confirm_alternate_upstream=True,
                expected_commit="not-a-full-commit",
            )

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "invalid_expected_commit")
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")

    def test_embedded_source_credentials_are_refused_without_echoing_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            private_value = "do-not-print-value"
            source_url = "https://" + "user:" + private_value + "@example.test/repository"
            result = updater.update_installation(install, source_url, str(SOURCE_PATH), "main")
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "source_credentials_refused")
            self.assertNotIn(private_value, result["source_repository"])
            self.assertNotIn(private_value, str(result["errors"]))

    def test_query_fragment_and_non_http_password_sources_are_refused_without_echo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            marker = "SYNTHETIC_" + "SOURCE_SECRET_45678"
            sources = (
                "https://example.test/repository?" + "access_" + "token=" + marker,
                "https://example.test/repository#" + marker,
                "ssh" + "://git:" + marker + "@example.test/repository",
            )
            for source_url in sources:
                with self.subTest(source_url=source_url.split(":", 1)[0]):
                    result = updater.update_installation(install, source_url, str(SOURCE_PATH), "main")
                    self.assertFalse(result["success"])
                    self.assertEqual(result["update_status"], "source_credentials_refused")
                    self.assertNotIn(marker, result["source_repository"])
                    self.assertNotIn(marker, str(result["errors"]))

    def test_git_failure_details_are_sanitized(self):
        marker = "SYNTHETIC_" + "GIT_ERROR_SECRET_11223"
        completed = subprocess.CompletedProcess(["git"], 1, stdout="", stderr="fatal: " + marker)
        with mock.patch.object(updater.subprocess, "run", return_value=completed):
            with self.assertRaises(updater.UpdateConflict) as error:
                updater._run_git("status")
        self.assertEqual(error.exception.code, "git_error")
        self.assertNotIn(marker, str(error.exception))

    def test_backup_inside_installation_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")
            expected = git(source, "rev-parse", "HEAD")
            result = updater.update_installation(
                install,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                backup_dir=install / "backups",
                confirm_alternate_upstream=True,
                expected_commit=expected,
            )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "unsafe_backup_path")
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")

    def test_backup_failure_returns_structured_error_without_replacing_installation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")
            expected = git(source, "rev-parse", "HEAD")
            original = (install / "SKILL.md").read_bytes()

            with mock.patch.object(updater.shutil, "copytree", side_effect=OSError("synthetic backup failure")):
                result = updater.update_installation(
                    install,
                    str(source),
                    str(SOURCE_PATH),
                    "main",
                    apply=True,
                    confirm_alternate_upstream=True,
                    expected_commit=expected,
                )

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "backup_failed")
            self.assertEqual((install / "SKILL.md").read_bytes(), original)

    def test_git_checkout_remote_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            checkout = root / "checkout"
            alternate = root / "alternate"
            subprocess.run(["git", "clone", "-q", str(source), str(checkout)], check=True)
            shutil.copytree(source, alternate)
            result = updater.update_installation(
                checkout / SOURCE_PATH,
                str(alternate),
                str(SOURCE_PATH),
                "main",
            )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "remote_mismatch")
            self.assertFalse(result["automatic_update_allowed"])
            self.assertEqual(result["next_agent_action"], "resolve_source_mismatch")

    def test_git_checkout_remote_mismatch_is_refused_when_content_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            checkout = root / "checkout"
            alternate = root / "alternate"
            subprocess.run(["git", "clone", "-q", str(source), str(checkout)], check=True)
            shutil.copytree(source, alternate)

            result = updater.update_installation(
                checkout / SOURCE_PATH,
                str(alternate),
                str(SOURCE_PATH),
                "main",
            )

            self.assertFalse(result["success"])
            self.assertFalse(result["skill_content_changed"])
            self.assertEqual(result["update_status"], "remote_mismatch")
            self.assertFalse(result["automatic_update_allowed"])

    def test_same_commit_with_ignored_skill_content_requires_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            (source / ".gitignore").write_text("skill/engineering-workflow/.runtime-cache\n", encoding="utf-8")
            git(source, "add", ".gitignore")
            git(source, "commit", "-q", "-m", "ignore runtime cache")
            checkout = root / "checkout"
            subprocess.run(["git", "clone", "-q", str(source), str(checkout)], check=True)
            (checkout / SOURCE_PATH / ".runtime-cache").write_text("local\n", encoding="utf-8")
            self.assertEqual(git(checkout, "status", "--porcelain"), "")

            result = updater.update_installation(
                checkout / SOURCE_PATH,
                str(source),
                str(SOURCE_PATH),
                "main",
            )

            self.assertFalse(result["success"])
            self.assertTrue(result["skill_content_changed"])
            self.assertFalse(result["automatic_update_allowed"])
            self.assertEqual(result["update_status"], "checkout_hidden_drift")
            self.assertEqual(result["next_agent_action"], "resolve_checkout_hidden_drift")

    def test_skip_worktree_skill_drift_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            checkout = root / "checkout"
            subprocess.run(["git", "clone", "-q", str(source), str(checkout)], check=True)
            relative = (SOURCE_PATH / "references" / "policy.md").as_posix()
            git(checkout, "update-index", "--skip-worktree", relative)
            (checkout / relative).write_text("hidden local edit\n", encoding="utf-8")
            self.assertEqual(git(checkout, "status", "--porcelain"), "")
            commit_version(source, "0.5.0")

            result = updater.update_installation(
                checkout / SOURCE_PATH,
                str(source),
                str(SOURCE_PATH),
                "main",
            )

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "checkout_hidden_drift")
            self.assertEqual(result["next_agent_action"], "resolve_checkout_hidden_drift")

    def test_canonical_remote_normalization(self):
        canonical = updater.CANONICAL_UPSTREAM
        self.assertTrue(updater.is_canonical_upstream(canonical))
        self.assertTrue(updater.is_canonical_upstream(canonical + ".git"))
        self.assertFalse(updater.is_canonical_upstream(canonical.replace("https://", "http://")))

    def test_source_commit_and_structured_fields_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            expected = commit_version(source, "0.5.0")
            result = updater.update_installation(install, str(source), str(SOURCE_PATH), "main")
            self.assertEqual(result["resolved_commit"], expected)
            for field in (
                "previous_version",
                "candidate_version",
                "source_repository",
                "source_path",
                "source_ref",
                "expected_commit",
                "active_installation_path",
                "resolved_target_path",
                "installation_type",
                "backup_path",
                "recovery_path",
                "validation_result",
                "skill_content_changed",
                "instructions_changed",
                "instruction_diff_summary",
                "version_change_kind",
                "major_or_minor_version_changed",
                "recommended_action",
                "next_agent_action",
                "automatic_update_allowed",
                "confirmation_required",
                "update_status",
                "reload_fallback",
                "restart_or_next_turn_required",
            ):
                self.assertIn(field, result)

    def test_diff_summary_includes_internal_symlink_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            link = source / SOURCE_PATH / "references" / "policy-link.md"
            link.symlink_to("policy.md")
            git(source, "add", ".")
            git(source, "commit", "-q", "-m", "add internal link")
            result = updater.update_installation(install, str(source), str(SOURCE_PATH), "main")
            self.assertTrue(result["success"], result)
            self.assertIn("references/policy-link.md", result["diff_summary"]["added"])

    def test_failed_copy_replacement_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")
            expected = git(source, "rev-parse", "HEAD")
            original_replace = os.replace
            calls = {"count": 0}

            def fail_second_replace(source_path, destination_path):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("simulated replacement failure")
                return original_replace(source_path, destination_path)

            with mock.patch.object(updater.os, "replace", side_effect=fail_second_replace):
                result = updater.update_installation(
                    install,
                    str(source),
                    str(SOURCE_PATH),
                    "main",
                    apply=True,
                    backup_dir=root / "backups",
                    confirm_alternate_upstream=True,
                    expected_commit=expected,
                )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "replacement_failed")
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")

    def test_failed_restore_preserves_backup_and_rollback_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            backups = root / "backups"
            shutil.copytree(source / SOURCE_PATH, install)
            expected = commit_version(source, "0.5.0")
            original_replace = os.replace
            calls = {"count": 0}

            def fail_install_and_restore(source_path, destination_path):
                calls["count"] += 1
                if calls["count"] in {2, 3}:
                    raise OSError("simulated replacement and restore failure")
                return original_replace(source_path, destination_path)

            with mock.patch.object(updater.os, "replace", side_effect=fail_install_and_restore):
                result = updater.update_installation(
                    install,
                    str(source),
                    str(SOURCE_PATH),
                    "main",
                    apply=True,
                    backup_dir=backups,
                    confirm_alternate_upstream=True,
                    expected_commit=expected,
                )

            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "rollback_failed")
            recovery = Path(result["recovery_path"])
            self.assertTrue(recovery.is_dir())
            self.assertEqual(updater.read_skill_identity(recovery)["version"], "0.4.1")
            backup_dirs = [path for path in backups.iterdir() if path.is_dir()]
            self.assertEqual(len(backup_dirs), 1)
            self.assertEqual(updater.read_skill_identity(backup_dirs[0])["version"], "0.4.1")


def init_catalog(
    root: Path, source: Path, version: str = "0.5.0", catalog_release: str = "1.0.0"
) -> tuple[Path, Path]:
    catalog = root / "catalog"
    catalog.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(catalog)], check=True)
    git(catalog, "config", "user.name", "Fixture")
    git(catalog, "config", "user.email", ('fixture' '@example.test'))
    bundle = catalog / "plugins" / "engineering-workflow"
    shutil.copytree(source / SOURCE_PATH, bundle / "skills" / "engineering-workflow")
    for platform in ("codex", "claude"):
        (bundle / f".{platform}-plugin").mkdir()
        (bundle / f".{platform}-plugin" / "plugin.json").write_text(
            json.dumps({"name": "engineering-workflow", "version": version}) + "\n"
        )
    provenance = {
        "schema_version": 1, "catalog_version": "1.0.0", "bundles": [{
            "name": "engineering-workflow", "version": version,
            "source_repository": updater.CANONICAL_UPSTREAM, "source_policy": "latest-tag",
            "source_ref": f"v{version}", "source_commit": git(source, "rev-parse", "HEAD"),
            "source_path": "plugins/engineering-workflow", "bundle_sha256": updater._bundle_digest(bundle),
        }],
    }
    (catalog / "PROVENANCE.json").write_text(json.dumps(provenance))
    git(catalog, "add", ".")
    git(catalog, "commit", "-q", "-m", "catalog release")
    git(catalog, "tag", "-a", f"v{catalog_release}", "-m", "stable")
    return catalog, bundle


class StableAndNativeUpdateTests(unittest.TestCase):
    def test_candidate_rejects_python_executable_cache_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = write_candidate(Path(tmp), "0.10.0")
            cache = candidate / "scripts" / "__pycache__"
            cache.mkdir()
            (cache / "tool.cpython-313.pyc").write_bytes(b"untrusted bytecode")
            with self.assertRaises(updater.UpdateConflict) as refusal:
                updater.validate_candidate(candidate)
            self.assertEqual(refusal.exception.code, "invalid_candidate_executable_cache")

    def test_cli_check_does_not_write_sibling_bytecode_when_environment_is_unset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root, "0.10.0")
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            runtime = root / "runtime"
            scripts = runtime / "scripts"
            assets = runtime / "assets"
            scripts.mkdir(parents=True)
            assets.mkdir()
            source_scripts = Path(updater.__file__).resolve().parent
            for name in ("update_installed_skill.py", "release_adoption.py", "common.py"):
                shutil.copy2(source_scripts / name, scripts / name)
            shutil.copy2(
                Path(updater.__file__).resolve().parents[1] / "assets" / "release_adoption.json",
                assets / "release_adoption.json",
            )
            environment = os.environ.copy()
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            completed = subprocess.run(
                [
                    str(Path(os.environ.get("PYTHON", sys.executable))),
                    str(scripts / "update_installed_skill.py"),
                    "--install-path", str(install),
                    "--source-repo", str(source),
                    "--source-path", str(SOURCE_PATH),
                    "--ref", "main", "--check", "--format", "json",
                ],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertFalse(any(path.name == "__pycache__" for path in runtime.rglob("__pycache__")))

    def test_modern_candidate_requires_capability_files_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = write_candidate(Path(tmp), "0.10.0")
            self.assertTrue(updater.validate_candidate(candidate)["success"])
            (candidate / "scripts" / "documentation_navigation.py").unlink()
            with self.assertRaises(updater.UpdateConflict) as refusal:
                updater.validate_candidate(candidate)
            self.assertEqual(refusal.exception.code, "invalid_candidate")

    def test_candidate_descriptor_preserves_bounded_semantic_summaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = write_candidate(Path(tmp), "0.10.0")
            descriptor = updater._candidate_descriptor(candidate)
            self.assertIsNotNone(descriptor)
            self.assertTrue(all(change.get("summary") for change in descriptor["changes"]))

    def test_modern_candidate_rejects_malformed_or_mismatched_descriptor(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = write_candidate(Path(tmp), "0.10.0")
            descriptor = candidate / "assets" / "release_adoption.json"
            for payload in ([], {"schema_version": 1, "skill_version": "0.10.0", "changes": []},
                            {"schema_version": 1, "skill_version": "0.9.10", "changes": []}):
                descriptor.write_text(json.dumps(payload))
                with self.assertRaises(updater.UpdateConflict) as refusal:
                    updater.validate_candidate(candidate)
                self.assertEqual(refusal.exception.code, "invalid_adoption_descriptor")

    def test_claude_marketplace_plain_output_is_not_parsed_as_json(self):
        completed = subprocess.CompletedProcess([], 0, "Marketplace refreshed\n", "")
        with mock.patch.object(updater.subprocess, "run", return_value=completed):
            result = updater._run_platform("claude", "plugin", "marketplace", "update", "xeonvs-engineering")
        self.assertEqual(result, {})

    def test_default_selects_annotated_stable_not_main_lightweight_or_prerelease(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root, "0.4.1")
            git(source, "tag", "-a", "v0.4.1", "-m", "release")
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")
            git(source, "tag", "v0.5.0")
            commit_version(source, "0.6.0-rc.1")
            git(source, "tag", "-a", "v0.6.0-rc.1", "-m", "preview")
            commit_version(source, "0.6.0")
            stable = updater.update_installation(install, str(source))
            development = updater.update_installation(install, str(source), ref="main")
            self.assertTrue(stable["success"], stable)
            self.assertEqual(stable["source_ref"], "v0.4.1")
            self.assertEqual(stable["candidate_version"], "0.4.1")
            self.assertEqual(development["candidate_version"], "0.6.0")

    def test_tag_version_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            git(source, "tag", "-a", "v0.5.0", "-m", "wrong version")
            install = root / "installed"
            shutil.copytree(source / SOURCE_PATH, install)
            result = updater.update_installation(install, str(source))
            self.assertEqual(result["update_status"], "release_version_mismatch")
            self.assertFalse(result["success"])

    def test_transport_failure_keeps_currentness_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install = write_candidate(root, "0.5.0")
            result = updater.update_installation(install, str(root / "absent"))
            self.assertEqual(result["update_status"], "upstream_unavailable")
            self.assertEqual(result["currentness"], "unknown")
            self.assertIsNone(result["candidate_version"])

    def _plugin_fixture(self, root: Path, catalog_release: str = "1.0.0"):
        source = init_upstream(root)
        install_bundle = root / "cache" / "old"
        install = install_bundle / "skills" / "engineering-workflow"
        shutil.copytree(source / SOURCE_PATH, install)
        (install_bundle / ".codex-plugin").mkdir()
        (install_bundle / ".codex-plugin" / "plugin.json").write_text("{}")
        commit_version(source, "0.5.0")
        git(source, "tag", "-a", "v0.5.0", "-m", "release")
        catalog, bundle = init_catalog(root, source, catalog_release=catalog_release)
        clone = updater._clone_candidate

        def local_clone(repo, path, ref, temporary):
            return clone(str(catalog if repo == updater.CANONICAL_MARKETPLACE else source), path, ref, temporary)
        return source, catalog, bundle, install, local_clone

    def test_catalog_lag_still_exposes_verified_deliverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root, "1.0.11")
            commit_version(source, "0.6.0")
            git(source, "tag", "-a", "v0.6.0", "-m", "new source release")
            before = updater._tree_entries(install)
            with mock.patch.object(updater, "_clone_candidate", side_effect=clone):
                result = updater.update_installation(install)
            self.assertTrue(result["success"], result)
            self.assertEqual(result["catalog_ref"], "v1.0.11")
            self.assertEqual(result["source_latest_version"], "0.6.0")
            self.assertEqual(result["candidate_version"], "0.5.0")
            self.assertTrue(result["delivery_pending"])
            self.assertEqual(result["recommended_action"], "marketplace_update")
            self.assertEqual(before, updater._tree_entries(install))

    def test_native_update_uses_cli_and_reads_back_new_active_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root, "1.0.10")
            new_bundle = root / "cache" / "new"
            shutil.copytree(bundle, new_bundle)
            source_commit = git(source, "rev-parse", "HEAD")
            catalog_commit = git(catalog, "rev-parse", "HEAD")
            inventory = {
                "pluginId": "engineering-workflow@xeonvs-engineering", "enabled": True, "version": "0.4.1",
                "installedPath": str(install.parent.parent),
                "source": {"source": "local", "path": str(bundle)},
                "marketplaceSource": {"sourceType": "git", "source": updater.CANONICAL_MARKETPLACE},
            }
            def platform_call(platform, *args):
                self.assertEqual(platform, "codex")
                if args[:2] == ("plugin", "list"):
                    return {"installed": [dict(inventory)]}
                if args[:2] == ("plugin", "add"):
                    inventory.update({"version": "0.5.0", "installedPath": str(new_bundle)})
                    return {"installedPath": str(new_bundle)}
                return {}
            before = updater._tree_entries(install)
            with mock.patch.object(updater, "_clone_candidate", side_effect=clone), mock.patch.object(
                updater, "_run_platform", side_effect=platform_call
            ), mock.patch.object(updater, "_replace_copied_installation", side_effect=AssertionError("cache write")):
                result = updater.update_installation(
                    install, apply=True, expected_commit=source_commit,
                    expected_catalog_commit=catalog_commit, platform="codex",
                )
            self.assertTrue(result["success"], result)
            self.assertEqual(result["catalog_ref"], "v1.0.10")
            self.assertTrue(result["native_readback_verified"])
            self.assertEqual(result["installed_version"], "0.5.0")
            self.assertEqual(before, updater._tree_entries(install))

    def test_codex_missing_inventory_path_uses_custom_home_for_check_and_native_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            codex_home = root / "custom-codex-home"
            install_bundle = (
                codex_home / "plugins" / "cache" / "xeonvs-engineering" / "engineering-workflow" / "0.4.1"
            )
            install = install_bundle / "skills" / "engineering-workflow"
            shutil.copytree(source / SOURCE_PATH, install)
            manifest = install_bundle / ".codex-plugin" / "plugin.json"
            manifest.parent.mkdir()
            manifest.write_text("{}\n")
            commit_version(source, "0.5.0")
            git(source, "tag", "-a", "v0.5.0", "-m", "release")
            catalog, bundle = init_catalog(root, source, catalog_release="1.0.10")
            new_bundle = install_bundle.parent / "0.5.0"
            shutil.copytree(bundle, new_bundle)
            clone = updater._clone_candidate

            def local_clone(repo, path, ref, temporary):
                return clone(str(catalog if repo == updater.CANONICAL_MARKETPLACE else source), path, ref, temporary)

            inventory = {
                "pluginId": "engineering-workflow@xeonvs-engineering", "enabled": True, "version": "0.4.1",
                "source": {"source": "local", "path": str(bundle)},
                "marketplaceSource": {"sourceType": "git", "source": updater.CANONICAL_MARKETPLACE},
            }

            def platform_call(platform, *args):
                if args[:2] == ("plugin", "list"):
                    return {"installed": [dict(inventory)]}
                if args[:2] == ("plugin", "add"):
                    inventory["version"] = "0.5.0"
                    return {"installedPath": str(new_bundle)}
                return {}

            with mock.patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}), mock.patch.object(
                updater, "_clone_candidate", side_effect=local_clone
            ), mock.patch.object(updater, "_run_platform", side_effect=platform_call):
                checked = updater.update_installation(install)
                result = updater.update_installation(
                    install,
                    apply=True,
                    expected_commit=checked["resolved_commit"],
                    expected_catalog_commit=checked["catalog_commit"],
                    platform="codex",
                )
            self.assertTrue(checked["success"], checked)
            self.assertTrue(result["success"], result)
            self.assertEqual(result["installed_version"], "0.5.0")
            self.assertEqual(result["path_resolution_evidence"]["before"]["source"], "codex_cache_layout")
            self.assertEqual(result["path_resolution_evidence"]["after"]["source"], "codex_cache_layout")
            self.assertEqual(result["active_installation_path"], str(new_bundle / "skills" / "engineering-workflow"))

    def test_delivery_provenance_rejects_catalog_release_as_format_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            commit_version(source, "0.5.0")
            catalog, _ = init_catalog(root, source, catalog_release="1.0.10")
            provenance = json.loads((catalog / "PROVENANCE.json").read_text())
            provenance["catalog_version"] = "1.0.10"
            with self.assertRaises(updater.UpdateConflict) as refusal:
                updater._delivery_provenance(json.dumps(provenance))
            self.assertEqual(refusal.exception.code, "invalid_delivery_provenance")

    def test_native_mismatch_fails_instead_of_reporting_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root)
            new_bundle = root / "cache" / "new"
            shutil.copytree(bundle, new_bundle)
            (new_bundle / "skills" / "engineering-workflow" / "SKILL.md").write_text("invalid active bytes\n")
            inventory = {
                "pluginId": "engineering-workflow@xeonvs-engineering", "enabled": True, "version": "0.4.1",
                "installedPath": str(install.parent.parent),
                "source": {"source": "local", "path": str(bundle)},
                "marketplaceSource": {"sourceType": "git", "source": updater.CANONICAL_MARKETPLACE},
            }
            def platform_call(platform, *args):
                if args[:2] == ("plugin", "list"):
                    return {"installed": [dict(inventory)]}
                if args[:2] == ("plugin", "add"):
                    inventory.update({"version": "0.5.0", "installedPath": str(new_bundle)})
                    return {"installedPath": str(new_bundle)}
                return {}
            with mock.patch.object(updater, "_clone_candidate", side_effect=clone), mock.patch.object(
                updater, "_run_platform", side_effect=platform_call
            ):
                result = updater.update_installation(
                    install, apply=True, expected_commit=git(source, "rev-parse", "HEAD"),
                    expected_catalog_commit=git(catalog, "rev-parse", "HEAD"), platform="codex",
                )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "native_post_update_mismatch")
            self.assertEqual(result["currentness"], "unknown")
            self.assertEqual(result["installed_version"], "0.5.0")
            self.assertNotEqual(result["active_installation_path"], str(install.absolute()))
            self.assertEqual(result["next_agent_action"], "recheck_native_installation_and_recover")

    def test_native_write_failure_recaptures_observed_active_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root)
            new_bundle = root / "cache" / "new"
            shutil.copytree(bundle, new_bundle)
            inventory = {
                "pluginId": "engineering-workflow@xeonvs-engineering", "enabled": True, "version": "0.4.1",
                "installedPath": str(install.parent.parent),
                "source": {"source": "local", "path": str(bundle)},
                "marketplaceSource": {"sourceType": "git", "source": updater.CANONICAL_MARKETPLACE},
            }

            def platform_call(platform, *args):
                if args[:2] == ("plugin", "list"):
                    return {"installed": [dict(inventory)]}
                if args[:3] == ("plugin", "marketplace", "upgrade"):
                    inventory.update({"version": "0.5.0", "installedPath": str(new_bundle)})
                    raise updater.UpdateConflict("native_update_failed", "Native plugin command failed")
                return {}

            with mock.patch.object(updater, "_clone_candidate", side_effect=clone), mock.patch.object(
                updater, "_run_platform", side_effect=platform_call
            ):
                result = updater.update_installation(
                    install, apply=True, expected_commit=git(source, "rev-parse", "HEAD"),
                    expected_catalog_commit=git(catalog, "rev-parse", "HEAD"), platform="codex",
                )
            self.assertEqual(result["update_status"], "native_update_failed")
            self.assertTrue(result["native_mutation_attempted"])
            self.assertFalse(result["native_readback_verified"])
            self.assertEqual(result["currentness"], "unknown")
            self.assertEqual(result["installed_version"], "0.5.0")
            self.assertEqual(
                result["active_installation_path"], str(new_bundle / "skills" / "engineering-workflow")
            )
            self.assertEqual(result["recommended_action"], "recheck_native_installation")
            self.assertEqual(result["next_agent_action"], "recheck_native_installation_and_recover")

    def test_native_readback_failure_clears_stale_active_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root)
            new_bundle = root / "cache" / "new"
            shutil.copytree(bundle, new_bundle)
            inventory = {
                "pluginId": "engineering-workflow@xeonvs-engineering", "enabled": True, "version": "0.4.1",
                "installedPath": str(install.parent.parent),
                "source": {"source": "local", "path": str(bundle)},
                "marketplaceSource": {"sourceType": "git", "source": updater.CANONICAL_MARKETPLACE},
            }
            inventory_reads = 0

            def platform_call(platform, *args):
                nonlocal inventory_reads
                if args[:2] == ("plugin", "list"):
                    inventory_reads += 1
                    if inventory_reads >= 3:
                        raise updater.UpdateConflict("native_result_invalid", "Native inventory unavailable")
                    return {"installed": [dict(inventory)]}
                if args[:2] == ("plugin", "add"):
                    inventory.update({"version": "0.5.0", "installedPath": str(new_bundle)})
                    return {"installedPath": str(new_bundle)}
                return {}

            with mock.patch.object(updater, "_clone_candidate", side_effect=clone), mock.patch.object(
                updater, "_run_platform", side_effect=platform_call
            ):
                result = updater.update_installation(
                    install, apply=True, expected_commit=git(source, "rev-parse", "HEAD"),
                    expected_catalog_commit=git(catalog, "rev-parse", "HEAD"), platform="codex",
                )
            self.assertEqual(result["update_status"], "native_result_invalid")
            self.assertTrue(result["native_mutation_attempted"])
            self.assertFalse(result["native_readback_verified"])
            self.assertEqual(result["currentness"], "unknown")
            self.assertIsNone(result["installed_version"])
            self.assertIsNone(result["active_installation_path"])
            self.assertIsNone(result["observed_native_path"])
            self.assertEqual(result["next_agent_action"], "recheck_native_installation_and_recover")

    def test_dual_manifest_bundle_refuses_other_platform_active_path_before_native_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root)
            claude_manifest = install.parent.parent / ".claude-plugin" / "plugin.json"
            claude_manifest.parent.mkdir()
            claude_manifest.write_text("{}\n")
            other_bundle = root / "cache" / "claude-active"
            shutil.copytree(install.parent.parent, other_bundle)
            inventory = {
                "id": "engineering-workflow@xeonvs-engineering", "enabled": True, "version": "0.4.1",
                "installPath": str(other_bundle), "scope": "local",
            }
            commands = []

            def platform_call(platform, *args):
                commands.append(args)
                if args[:2] == ("plugin", "list"):
                    return [dict(inventory)]
                raise AssertionError(f"unexpected native mutation: {args}")

            with mock.patch.object(updater, "_clone_candidate", side_effect=clone), mock.patch.object(
                updater, "_run_platform", side_effect=platform_call
            ):
                result = updater.update_installation(
                    install, apply=True, expected_commit=git(source, "rev-parse", "HEAD"),
                    expected_catalog_commit=git(catalog, "rev-parse", "HEAD"), platform="claude",
                )
            self.assertEqual(result["update_status"], "native_active_identity_mismatch")
            self.assertEqual(commands, [("plugin", "list", "--json")])

    def test_native_active_python_cache_refuses_before_native_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root)
            cache = install / "scripts" / "__pycache__"
            cache.mkdir()
            (cache / "tool.cpython-313.pyc").write_bytes(b"runtime bytecode")
            inventory = {
                "pluginId": "engineering-workflow@xeonvs-engineering", "enabled": True, "version": "0.4.1",
                "installedPath": str(install.parent.parent),
                "source": {"source": "local", "path": str(bundle)},
                "marketplaceSource": {"sourceType": "git", "source": updater.CANONICAL_MARKETPLACE},
            }
            commands = []

            def platform_call(platform, *args):
                commands.append(args)
                return {"installed": [dict(inventory)]}

            with mock.patch.object(updater, "_clone_candidate", side_effect=clone), mock.patch.object(
                updater, "_run_platform", side_effect=platform_call
            ):
                result = updater.update_installation(
                    install, apply=True, expected_commit=git(source, "rev-parse", "HEAD"),
                    expected_catalog_commit=git(catalog, "rev-parse", "HEAD"), platform="codex",
                )
            self.assertEqual(result["update_status"], "native_active_executable_cache")
            self.assertEqual(result["next_agent_action"], "reinstall_native_plugin_without_direct_cache_edits")
            self.assertEqual(
                commands,
                [("plugin", "list", "--marketplace", "xeonvs-engineering", "--json")],
            )

    def test_native_apply_requires_reviewed_delivery_pins_before_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root)
            with mock.patch.object(updater, "_clone_candidate", side_effect=clone), mock.patch.object(
                updater, "_run_platform"
            ) as native:
                result = updater.update_installation(install, apply=True, platform="codex")
            self.assertEqual(result["update_status"], "expected_delivery_mismatch")
            native.assert_not_called()

    def test_claude_native_update_checks_canonical_marketplace_and_readback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root)
            metadata = install.parent.parent / ".claude-plugin" / "plugin.json"
            metadata.parent.mkdir()
            metadata.write_text("{}")
            new_bundle = root / "cache" / "new"
            shutil.copytree(bundle, new_bundle)
            inventory = {
                "id": "engineering-workflow@xeonvs-engineering", "enabled": True, "version": "0.4.1",
                "installPath": str(install.parent.parent), "scope": "project",
            }
            commands = []
            def platform_call(platform, *args):
                commands.append(args)
                if args[:3] == ("plugin", "marketplace", "list"):
                    return [{"name": "xeonvs-engineering", "source": "github",
                             "repo": "xeonvs/xeonvs-engineering", "installLocation": str(catalog)}]
                if args[:2] == ("plugin", "list"):
                    return [dict(inventory)]
                if args[:2] == ("plugin", "update"):
                    inventory.update({"version": "0.5.0", "installPath": str(new_bundle)})
                return {}
            with mock.patch.object(updater, "_clone_candidate", side_effect=clone), mock.patch.object(
                updater, "_run_platform", side_effect=platform_call
            ):
                result = updater.update_installation(
                    install, apply=True, expected_commit=git(source, "rev-parse", "HEAD"),
                    expected_catalog_commit=git(catalog, "rev-parse", "HEAD"), platform="claude",
                )
            self.assertTrue(result["success"], result)
            self.assertTrue(result["native_readback_verified"])
            self.assertIn(("plugin", "marketplace", "update", "xeonvs-engineering"), commands)
            self.assertIn(
                (
                    "plugin", "update", "engineering-workflow@xeonvs-engineering",
                    "--scope", "project", "--json",
                ),
                commands,
            )

    def test_native_changed_marketplace_snapshot_refuses_plugin_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, catalog, bundle, install, clone = self._plugin_fixture(root)
            provenance_path = catalog / "PROVENANCE.json"
            provenance = json.loads(provenance_path.read_text())
            provenance["bundles"][0]["source_commit"] = "0" * 40
            provenance_path.write_text(json.dumps(provenance))
            inventory = {
                "pluginId": "engineering-workflow@xeonvs-engineering", "enabled": True, "version": "0.4.1",
                "installedPath": str(install.parent.parent),
                "source": {"source": "local", "path": str(bundle)},
                "marketplaceSource": {"sourceType": "git", "source": updater.CANONICAL_MARKETPLACE},
            }
            commands = []
            def platform_call(platform, *args):
                commands.append(args)
                return {"installed": [dict(inventory)]} if args[:2] == ("plugin", "list") else {}
            with mock.patch.object(updater, "_clone_candidate", side_effect=clone), mock.patch.object(
                updater, "_run_platform", side_effect=platform_call
            ):
                result = updater.update_installation(
                    install, apply=True, expected_commit=git(source, "rev-parse", "HEAD"),
                    expected_catalog_commit=git(catalog, "rev-parse", "HEAD"), platform="codex",
                )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "native_delivery_mismatch")
            self.assertFalse(any(args[:2] == ("plugin", "add") for args in commands))


if __name__ == "__main__":
    unittest.main()
