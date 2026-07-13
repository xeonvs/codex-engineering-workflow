from __future__ import annotations

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
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")

    def test_copied_install_apply_creates_backup_and_replaces_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            install = root / "installed"
            backup_root = root / "backups"
            shutil.copytree(source / SOURCE_PATH, install)
            commit_version(source, "0.5.0")
            result = updater.update_installation(
                install,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                backup_dir=backup_root,
                confirm_alternate_upstream=True,
            )
            self.assertTrue(result["success"], result)
            self.assertEqual(result["installation_type"], "copied")
            self.assertEqual(result["update_status"], "updated")
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.5.0")
            backup = Path(result["backup_path"])
            self.assertTrue(backup.is_dir())
            self.assertEqual(updater.read_skill_identity(backup)["version"], "0.4.1")

    def test_symlink_install_preserves_link_and_updates_resolved_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = init_upstream(root)
            target = root / "target"
            link = root / "active-skill"
            shutil.copytree(source / SOURCE_PATH, target)
            link.symlink_to(target, target_is_directory=True)
            commit_version(source, "0.5.0")
            result = updater.update_installation(
                link,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                backup_dir=root / "backups",
                confirm_alternate_upstream=True,
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
            (checkout / SOURCE_PATH / "references" / "policy.md").write_text("local edit\n", encoding="utf-8")
            result = updater.update_installation(
                checkout / SOURCE_PATH,
                str(source),
                str(SOURCE_PATH),
                "main",
                apply=True,
                confirm_alternate_upstream=True,
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

    def test_backup_inside_installation_is_refused(self):
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
                backup_dir=install / "backups",
                confirm_alternate_upstream=True,
            )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "unsafe_backup_path")
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")

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

    def test_canonical_remote_normalization(self):
        canonical = updater.CANONICAL_UPSTREAM
        self.assertTrue(updater.is_canonical_upstream(canonical))
        self.assertTrue(updater.is_canonical_upstream(canonical + ".git"))

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
                "active_installation_path",
                "resolved_target_path",
                "installation_type",
                "validation_result",
                "update_status",
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
                )
            self.assertFalse(result["success"])
            self.assertEqual(result["update_status"], "replacement_failed")
            self.assertEqual(updater.read_skill_identity(install)["version"], "0.4.1")


if __name__ == "__main__":
    unittest.main()
