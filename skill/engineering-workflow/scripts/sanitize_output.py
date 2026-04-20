#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ISSUE_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "internal_hostname": re.compile(r"\b[a-zA-Z0-9.-]+\.(internal|corp|local)\b"),
    "absolute_home_path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "credential_like_assignment": re.compile(
        r"\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[A-Za-z0-9._-]{8,}",
        re.IGNORECASE,
    ),
}


def scan_text(text: str, deny_terms: list[str] | None = None) -> list[dict[str, str]]:
    issues = []
    for name, pattern in ISSUE_PATTERNS.items():
        match = pattern.search(text)
        if match:
            issues.append({"type": name, "match": match.group(0)})
    for term in deny_terms or []:
        if term and term.lower() in text.lower():
            issues.append({"type": "deny_term", "match": term})
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan proposed outputs for sensitive or project-specific content.")
    parser.add_argument("--path", action="append", default=[], help="File path to scan")
    parser.add_argument("--deny-term", action="append", default=[], help="Forbidden term to scan for")
    args = parser.parse_args()

    texts = []
    if args.path:
        for raw_path in args.path:
            path = Path(raw_path)
            texts.append(path.read_text(encoding="utf-8"))
    else:
        texts.append(sys.stdin.read())

    issues = []
    for text in texts:
        issues.extend(scan_text(text, args.deny_term))

    print(json.dumps({"success": not issues, "issues": issues}, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
