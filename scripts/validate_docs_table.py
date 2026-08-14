#!/usr/bin/env python3
"""Validate that docs/*.md files match the docs table in README.md.

Lightweight, no network. Fails (exit 1) when a docs/ file is missing from the
README docs table, or the table lists a doc that does not exist. Run in CI so
renames/additions stay in sync.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
DOCS = os.path.join(ROOT, "docs")


def docs_table_rows(text: str) -> list:
    rows = []
    in_docs = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_docs = line == "## Docs"
            continue
        if in_docs and line.startswith("|"):
            rows.append(line)
    return rows


def main() -> int:
    with open(README) as fh:
        text = fh.read()

    table_docs = set()
    for row in docs_table_rows(text):
        for match in re.finditer(r"`([A-Za-z0-9][^`]*\.md)`", row):
            table_docs.add(match.group(1))

    actual = {name for name in os.listdir(DOCS) if name.endswith(".md")}

    missing_from_table = sorted(actual - table_docs)
    missing_file = sorted(table_docs - actual)

    if not missing_from_table and not missing_file:
        print(f"docs table OK ({len(actual)} docs, {len(table_docs)} table rows)")
        return 0

    if missing_from_table:
        print("docs files missing from README table:", ", ".join(missing_from_table))
    if missing_file:
        print("README table entries with no docs/ file:", ", ".join(missing_file))
    return 1


if __name__ == "__main__":
    sys.exit(main())
