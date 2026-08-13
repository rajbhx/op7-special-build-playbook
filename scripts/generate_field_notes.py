#!/usr/bin/env python3
"""Regenerate docs/09-field-notes-journey.md from the machine-readable log.

Usage: generate_field_notes.py <log.yml> <output.md>
The log.yml source lives in rajbhx/iceraven-op7 (docs/field-notes/log.yml) and
is fetched by .github/workflows/playbook-sync.yml before this script runs.
"""
import sys
import yaml

def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: generate_field_notes.py <log.yml> <output.md>")
    log_path, out_path = sys.argv[1], sys.argv[2]
    with open(log_path) as f:
        data = yaml.safe_load(f)

    lines = []
    lines.append("# 09 — Field notes: problems we actually hit and how we solved them")
    lines.append("")
    lines.append("> Auto-generated from `docs/field-notes/log.yml` in `rajbhx/iceraven-op7`")
    lines.append("> by `.github/workflows/playbook-sync.yml`. Do not edit by hand.")
    lines.append("> Add/update entries in the source log; the next sync regenerates this file.")
    lines.append("")
    lines.append("Chronological log from the Iceraven OP7 project. Reusable for any app.")
    lines.append("")
    for section in data.get("sections", []):
        lines.append(f"## {section['id']}. {section['title']}")
        lines.append("")
        lines.append("| # | Problem | Root cause | Solution |")
        lines.append("|---|---|---|---|")
        for entry in section.get("entries", []):
            problem = entry["problem"].replace("|", "\\|")
            cause = entry["cause"].replace("|", "\\|")
            solution = entry["solution"].replace("|", "\\|")
            lines.append(f"| {entry['id']} | {problem} | {cause} | {solution} |")
        lines.append("")
    sig = data.get("recurring_signature", "").strip()
    if sig:
        lines.append("## Recurring failure signature")
        lines.append("")
        lines.append(sig)
        lines.append("")
    lines.append("<!-- generated; do not hand-edit -->")
    with open(out_path, "w") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"wrote {out_path}")

if __name__ == "__main__":
    main()
