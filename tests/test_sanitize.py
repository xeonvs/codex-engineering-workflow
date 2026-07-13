from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from test_support import load_script_module


sanitize_output = load_script_module("sanitize_output")


class SanitizeTests(unittest.TestCase):
    def test_detects_private_signals(self):
        path = "/" + "home" + "/example/work"
        assignment = "to" + "ken" + "=" + "abc123456789"
        email = "privacy" + "@" + "example.com"
        text = f"email {email} and path {path} plus {assignment}"
        issues = sanitize_output.scan_text(text)
        issue_types = {item["type"] for item in issues}
        self.assertIn("email", issue_types)
        self.assertIn("linux_user_path", issue_types)
        self.assertIn("credential_like_assignment", issue_types)

    def test_shared_scanner_detects_bearer_environment_secret_and_email(self):
        bearer = "Bearer" + " " + ("A" * 24)
        environment_secret = "AWS_" + "SECRET_ACCESS_KEY" + "=" + ("B" * 24)
        email = "person" + "@" + "private.example"
        findings = sanitize_output.scan_text("\n".join((bearer, environment_secret, email)))
        kinds = {item["type"] for item in findings}
        self.assertIn("bearer_token", kinds)
        self.assertIn("environment_secret_assignment", kinds)
        self.assertIn("email", kinds)

    def test_detects_every_supported_path_and_host_family(self):
        mac = "/" + "Users" + "/sample/work"
        linux = "/" + "home" + "/sample/work"
        windows = "C:" + "\\" + "Users" + "\\sample\\work"
        file_url = "file" + "://" + "/tmp/report"
        ssh_path = "/" + "home" + "/sample/" + ".ssh" + "/id_ed25519"
        host = "build" + ".internal"
        findings = sanitize_output.scan_text("\n".join((mac, linux, windows, file_url, ssh_path, host)))
        kinds = {item["type"] for item in findings}
        self.assertTrue(
            {
                "macos_user_path",
                "linux_user_path",
                "windows_user_path",
                "file_url",
                "private_ssh_key_path",
                "internal_hostname",
            }.issubset(kinds)
        )

    def test_detects_known_key_material_without_returning_value(self):
        marker = "BEGIN " + "OPENSSH " + "PRIVATE KEY"
        prefix_value = "gh" + "p_" + ("A" * 24)
        findings = sanitize_output.scan_text(marker + "\n" + prefix_value)
        kinds = {item["type"] for item in findings}
        self.assertIn("private_key_material", kinds)
        self.assertIn("known_token_prefix", kinds)
        self.assertTrue(all(set(item) <= {"type", "line"} for item in findings))

    def test_public_tree_scan_includes_root_plans(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_path = "/" + "Users" + "/sample/project"
            private_email = "person" + "@" + "private.example"
            (root / "PLANS.md").write_text(private_path, encoding="utf-8")
            (root / "CONTACT.md").write_text(private_email, encoding="utf-8")
            findings = sanitize_output.scan_public_tree(root)
            self.assertTrue(any(item["path"] == "PLANS.md" and item["type"] == "macos_user_path" for item in findings))
            self.assertTrue(any(item["path"] == "CONTACT.md" and item["type"] == "email" for item in findings))

    def test_public_tree_scan_does_not_follow_external_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "repo"
            root.mkdir()
            outside = base / "outside.txt"
            key_name = "pass" + "word"
            outside.write_text(key_name + "=" + "not-for-publication", encoding="utf-8")
            (root / "linked.txt").symlink_to(Path("..") / outside.name)
            self.assertEqual(sanitize_output.scan_public_tree(root), [])

    def test_tracked_ignored_text_is_scanned_but_untracked_ignored_text_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / ".gitignore").write_text("vendor/\n", encoding="utf-8")
            tracked = root / "vendor" / "tracked.md"
            untracked = root / "vendor" / "untracked.md"
            tracked.parent.mkdir()
            tracked.write_text("/" + "Users" + "/sample/tracked\n", encoding="utf-8")
            untracked.write_text("/" + "Users" + "/sample/untracked\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", ".gitignore"], check=True)
            subprocess.run(["git", "-C", str(root), "add", "-f", "vendor/tracked.md"], check=True)

            findings = sanitize_output.scan_public_tree(root)

            paths = {item["path"] for item in findings}
            self.assertIn("vendor/tracked.md", paths)
            self.assertNotIn("vendor/untracked.md", paths)

    def test_historical_version_is_not_a_privacy_finding(self):
        self.assertEqual(sanitize_output.scan_text("Recently completed release 0.4.1."), [])

    def test_line_numbers_do_not_depend_on_repeated_prefix_counting(self):
        class CountForbiddenText(str):
            def count(self, *_args, **_kwargs):
                raise AssertionError("privacy line calculation must not rescan prefixes")

        text = CountForbiddenText("first\n/" + "home" + "/sample/private\n")
        findings = sanitize_output.scan_text(text)
        self.assertTrue(any(item["line"] == 2 for item in findings))

    def test_detects_deny_terms(self):
        issues = sanitize_output.scan_text("forbidden project name", deny_terms=["forbidden"])
        self.assertTrue(any(item["type"] == "deny_term" for item in issues))


if __name__ == "__main__":
    unittest.main()
