from __future__ import annotations

import unittest

from test_support import load_script_module


sanitize_output = load_script_module("sanitize_output")


class SanitizeTests(unittest.TestCase):
    def test_detects_private_signals(self):
        text = ('email user' '@example.test and path /h' 'ome/example/work plus to' 'ken=abc123456789')
        issues = sanitize_output.scan_text(text)
        issue_types = {item["type"] for item in issues}
        self.assertIn("email", issue_types)
        self.assertIn("absolute_home_path", issue_types)
        self.assertIn("credential_like_assignment", issue_types)

    def test_detects_deny_terms(self):
        issues = sanitize_output.scan_text("forbidden project name", deny_terms=["forbidden"])
        self.assertTrue(any(item["type"] == "deny_term" for item in issues))


if __name__ == "__main__":
    unittest.main()
