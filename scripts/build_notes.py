#!/usr/bin/env python3
"""Build the low-token, searchable notes layer for the playbook.

Usage: build_notes.py <logs-dir>
  <logs-dir>               one <slug>.yml per project (fetched logs) plus
                           sessions/ (<logs-dir>/sessions/<slug>/*.md)

Reads:
  <logs-dir>/<slug>.yml           machine-readable field notes (fetched)
  <logs-dir>/sessions/<slug>/*.md conversation digests (fetched)

Writes (relative to the playbook repo root):
  docs/09-field-notes-journey.md   human journey (first project with a log)
  notes/README.md                  agent-facing usage guide
  notes/<slug>/INDEX.md            compact keyword -> entry ids map (grep me)
  notes/<slug>/index.json          machine-readable index (for lookup.py)
  notes/<slug>/entries/<id>.md     one file per entry
  notes/<slug>/SESSIONS.md         conversation digest list

All notes output is generated; never hand-edit it. The source of truth is
each project's docs/field-notes/log.yml.
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STOPWORDS = {
    "add", "added", "all", "already", "always", "are", "best", "can", "does",
    "down", "etc", "ever", "file", "files", "for", "from", "full", "get",
    "got", "has", "have", "into", "its", "keep", "last", "like", "made",
    "make", "makes", "many", "more", "most", "much", "must", "need", "never",
    "next", "not", "now", "only", "out", "over", "per", "run", "see", "some",
    "than", "that", "the", "then", "this", "those", "time", "times", "used",
    "very", "was", "way", "when", "where", "which", "will", "with", "you",
    "your", "first", "second", "also", "even", "just", "both", "each",
    "every", "other", "such", "take", "while", "without", "after", "before",
    "during", "between", "under", "again", "across", "along", "among",
    "around", "through", "until", "upon", "get", "got", "would", "could",
    "should", "may", "might", "via", "one", "two", "way", "well",
}


def esc_table(value: str) -> str:
    return value.replace("|", "\\|")


def tokenize(text: str) -> list:
    words = re.findall(r"[a-z0-9][a-z0-9+._-]*", text.lower())
    out = []
    for w in words:
        w = w.strip("._-")
        if len(w) >= 3 and w not in STOPWORDS and not w.isdigit():
            out.append(w)
    return out


def clean_keywords(tokens: set, tags: set) -> list:
    tokens = {w for w in tokens if w[0].isalpha() and (len(w) >= 4 or w in tags)}
    order = sorted(tokens, key=lambda w: (-len(w), w))
    kept = set()
    for kw in order:
        if kw not in tags and any(k != kw and k.startswith(kw) and len(k) - len(kw) <= 4 for k in tokens):
            continue
        kept.add(kw)
    return sorted(tags | kept)


def derive_keywords(entry: dict, section_title: str) -> list:
    """Full-text keywords (problem+cause+solution) for entry files and index.json."""
    tags = {t.lower() for t in entry.get("tags", [])}
    tokens = set(tokenize(f"{entry['problem']} {entry['cause']} {entry['solution']} {section_title}"))
    return clean_keywords(tokens, tags)


def derive_index_keywords(entry: dict, section_title: str) -> list:
    """Compact curated set for INDEX.md: tags + problem-text words only."""
    tags = {t.lower() for t in entry.get("tags", [])}
    tokens = set(tokenize(f"{entry['problem']} {section_title}"))
    return clean_keywords(tokens, tags)


def render_journey(lines: list, log: dict) -> None:
    for section in log.get("sections", []):
        lines.append(f"### {section['id']}. {section['title']}")
        lines.append("")
        lines.append("| # | Problem | Root cause | Solution |")
        lines.append("|---|---|---|---|")
        for entry in section.get("entries", []):
            lines.append(f"| {entry['id']} | {esc_table(entry['problem'])} | "
                         f"{esc_table(entry['cause'])} | {esc_table(entry['solution'])} |")
        lines.append("")
    sig = (log.get("recurring_signature") or "").strip()
    if sig:
        lines.append("### Recurring failure signature")
        lines.append("")
        lines.append(sig)
        lines.append("")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: build_notes.py <logs-dir>")
    logs_dir = sys.argv[1]
    slugs = sorted(os.path.basename(m)[:-4] for m in glob.glob(os.path.join(logs_dir, "*.yml")))
    if not slugs:
        print("no logs found; nothing to build")
        return

    notes_root = os.path.join(ROOT, "notes")
    os.makedirs(notes_root, exist_ok=True)

    journey_src = None
    for slug in slugs:
        log_path = os.path.join(logs_dir, f"{slug}.yml")
        with open(log_path) as f:
            log = yaml.safe_load(f)
        if not log or not log.get("sections"):
            continue
        if journey_src is None:
            journey_src = (slug, log)

        entries = []
        for section in log["sections"]:
            for entry in section.get("entries", []):
                entry.setdefault("tags", [])
                keywords = derive_keywords(entry, section["title"])
                entries.append({
                    "id": entry["id"],
                    "section": section["id"],
                    "section_title": section["title"],
                    "problem": entry["problem"],
                    "cause": entry["cause"],
                    "solution": entry["solution"],
                    "tags": entry["tags"],
                    "keywords": keywords,
                    "index_keywords": derive_index_keywords(entry, section["title"]),
                })
        entries.sort(key=lambda e: e["id"])

        slug_notes = os.path.join(notes_root, slug)
        entries_dir = os.path.join(slug_notes, "entries")
        os.makedirs(entries_dir, exist_ok=True)

        # per-entry markdown files (read only the one you need)
        for e in entries:
            lines = [
                f"# {e['id']} — {e['problem']}",
                "",
                f"**Section**: {e['section']}. {e['section_title']}",
                "**Keywords**: " + ", ".join(e["keywords"]),
                "",
                "## Problem",
                "",
                e["problem"],
                "",
                "## Root cause",
                "",
                e["cause"],
                "",
                "## Solution",
                "",
                e["solution"],
                "",
                "<!-- generated by build_notes.py; do not hand-edit -->",
            ]
            with open(os.path.join(entries_dir, f"{e['id']}.md"), "w") as f:
                f.write("\n".join(lines) + "\n")

        # keyword -> ids index (compact, grep-able)
        kw_map = defaultdict(list)
        for e in entries:
            for kw in e["index_keywords"]:
                kw_map[kw].append(e["id"])
        index_lines = [
            f"# Notes index — {slug}",
            "",
            f"> {len(entries)} entries, {len(kw_map)} search terms (tags + problem words). One per line.",
            "> Generated by `scripts/build_notes.py`. Search this file with grep,",
            "> or use `python3 scripts/lookup.py <words...>` for ranked matches.",
            "",
        ]
        for kw in sorted(kw_map):
            ids = kw_map[kw]
            shown = " ".join(ids[:6])
            if len(ids) > 6:
                shown += f" …+{len(ids) - 6}"
            index_lines.append(f"{kw}: {shown}")
        with open(os.path.join(slug_notes, "INDEX.md"), "w") as f:
            f.write("\n".join(index_lines) + "\n")

        # machine-readable index for lookup.py
        with open(os.path.join(slug_notes, "index.json"), "w") as f:
            json.dump({"slug": slug, "entries": entries}, f, indent=1)

        # session digests
        sessions = sorted(p for p in glob.glob(os.path.join(logs_dir, "sessions", slug, "*.md"))
                         if not os.path.basename(p).startswith("_"))
        if sessions:
            sess_lines = [
                f"# Session digests — {slug}",
                "",
                "Conversation digests captured by the `session_to_notes` pipeline",
                "in the build repo. Synced copies for offline search.",
                "",
                "| File | Summary |",
                "|---|---|",
            ]
            for sp in sessions:
                name = os.path.basename(sp)
                summary = ""
                with open(sp) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#"):
                            summary = line.lstrip("# ").strip()[:120]
                            break
                        if line and not summary:
                            summary = line[:120]
                sess_lines.append(f"| {name} | {esc_table(summary)} |")
            sess_lines.append("")
            with open(os.path.join(slug_notes, "SESSIONS.md"), "w") as f:
                f.write("\n".join(sess_lines))

        # conversation knowledge (typed, extracted by conversation_to_notes.py)
        convos = sorted(p for p in glob.glob(os.path.join(logs_dir, "conversations", slug, "*.md"))
                        if not os.path.basename(p).startswith("_"))
        if convos:
            conv_lines = [
                f"# Conversation knowledge — {slug}",
                "",
                "User instructions/decisions extracted from Codex sessions as typed",
                "entries (RULE/DECISION/REQUEST/GOTCHA/GOAL). Raw transcripts are",
                "never stored — only the useful learned types.",
                "",
                "| File | First entries |",
                "|---|---|",
            ]
            for cp in convos:
                name = os.path.basename(cp)
                preview = []
                with open(cp) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("- `") and len(preview) < 2:
                            preview.append(line[:110])
                conv_lines.append(f"| {name} | {'<br>'.join(preview) or '—'} |")
            conv_lines.append("")
            with open(os.path.join(slug_notes, "CONVERSATIONS.md"), "w") as f:
                f.write("\n".join(conv_lines))

        print(f"notes: {slug} — {len(entries)} entries, {len(kw_map)} keywords, "
              f"{len(sessions)} session(s), {len(convos)} conversation(s)")

    # agent-facing usage guide
    guide = [
        "# Notes layer — low-token lookup for AI agents",
        "",
        "Search before reading. The journey table (`docs/09-*`) is for humans;",
        "agents should use this layer to find exactly one entry and read only that.",
        "",
        "```bash",
        "python3 scripts/lookup.py install testonly    # ranked matches, one line each",
        "python3 scripts/lookup.py --id C1             # full detail for one entry",
        "python3 scripts/lookup.py --sessions          # conversation digests",
        "python3 scripts/lookup.py --tags              # all search tags",
        "grep -i install notes/*/INDEX.md              # ultra-cheap fallback, no python",
        "```",
        "",
        "Layout:",
        "",
        "- `notes/<slug>/INDEX.md` — keyword → entry ids (grep this first)",
        "- `notes/<slug>/entries/<id>.md` — one problem+solution per file",
        "- `notes/<slug>/SESSIONS.md` — conversation digests synced from the build repo",
        "- `notes/<slug>/index.json` — machine-readable index for `lookup.py`",
        "",
        "Everything here is generated by `scripts/build_notes.py` from each project's",
        "`docs/field-notes/log.yml`. Do not hand-edit generated files.",
        "",
    ]
    with open(os.path.join(notes_root, "README.md"), "w") as f:
        f.write("\n".join(guide))

    # human journey (first project with a log)
    if journey_src:
        slug, log = journey_src
        lines = [
            "# 09 — Field notes: problems we actually hit and how we solved them",
            "",
            f"> Auto-generated from `docs/field-notes/log.yml` in the `{slug}` build repo",
            f"> by `.github/workflows/playbook-sync.yml` -> `scripts/build_notes.py`. Do not hand-edit.",
            "> For agent use, search the compact layer: `scripts/lookup.py <words>` or",
            "> grep `notes/" + slug + "/INDEX.md`.",
            "",
            "Chronological log from the field. Reusable for any app.",
            "",
        ]
        render_journey(lines, log)
        lines.append("<!-- generated; do not hand-edit -->")
        out_path = os.path.join(ROOT, "docs", "09-field-notes-journey.md")
        with open(out_path, "w") as f:
            f.write("\n".join(lines).rstrip() + "\n")
        print(f"journey: docs/09-field-notes-journey.md ({slug})")

    print("done")


if __name__ == "__main__":
    main()
