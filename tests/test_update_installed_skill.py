from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
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
    def test_plugin_managed_install_returns_marketplace_handoff_without_cache_write(self):
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

            result = updater.update_installation(
                install,
                "https://invalid.example.test/should-not-be-fetched",
                str(SOURCE_PATH),
                "main",
                apply=True,
            )

            after = {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()}
            self.assertTrue(result["success"], result)
            self.assertEqual(result["installation_type"], "plugin_managed")
            self.assertEqual(result["update_status"], "marketplace_handoff")
            self.assertEqual(result["recommended_action"], "marketplace_update")
            self.assertEqual(result["next_agent_action"], "update_plugin_through_marketplace")
            self.assertFalse(result["marketplace_handoff"]["direct_cache_replacement_allowed"])
            self.assertEqual(result["marketplace_handoff"]["platforms"], ["codex", "claude"])
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


if __name__ == "__main__":
    unittest.main()
