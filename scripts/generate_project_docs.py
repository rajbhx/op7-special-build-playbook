#!/usr/bin/env python3
"""Generate per-project journey docs + index from manifests and fetched logs.

Usage: generate_project_docs.py <logs-dir>
  <logs-dir>  directory with one <slug>.yml per project (fetched by the sync
              workflow from each project's field_notes.repo/path)

Outputs (relative to the playbook repo root):
  projects/<slug>/README.md   project card + problems->solutions journey
  projects/README.md          generated index of all projects

Projects without a log file in <logs-dir> still get a card (journey section
is skipped with a note).
"""
import glob
import os
import sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def esc(value: str) -> str:
    return value.replace("|", "\\|")

def render_journey(lines, log: dict) -> None:
    for section in log.get("sections", []):
        lines.append(f"### {section['id']}. {section['title']}")
        lines.append("")
        lines.append("| # | Problem | Root cause | Solution |")
        lines.append("|---|---|---|---|")
        for entry in section.get("entries", []):
            lines.append(f"| {entry['id']} | {esc(entry['problem'])} | {esc(entry['cause'])} | {esc(entry['solution'])} |")
        lines.append("")
    sig = (log.get("recurring_signature") or "").strip()
    if sig:
        lines.append("### Recurring failure signature")
        lines.append("")
        lines.append(sig)
        lines.append("")

def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: generate_project_docs.py <logs-dir>")
    logs_dir = sys.argv[1]
    manifests = sorted(glob.glob(os.path.join(ROOT, "projects", "*", "manifest.yml")))
    manifests = [m for m in manifests if "template" not in m]

    index = ["# Projects", "",
             "Auto-generated index. Register new builds by adding a manifest;",
             "see `AGENTS.md` for the schema and workflow.", ""]
    for manifest in manifests:
        slug = os.path.basename(os.path.dirname(manifest))
        with open(manifest) as f:
            proj = yaml.safe_load(f)["project"]
        log_path = os.path.join(logs_dir, f"{slug}.yml")
        log = None
        if os.path.isfile(log_path):
            with open(log_path) as f:
                log = yaml.safe_load(f)
        lines = [
            f"# {proj['name']}",
            "",
            f"> Auto-generated from `projects/{slug}/manifest.yml` and the",
            f"> project's field-notes log. Do not hand-edit the journey section.",
            "",
            "## Project",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Description | {esc(proj.get('description',''))} |",
            f"| Build repo | {proj.get('repo','')} |",
            f"| Upstream | {proj.get('upstream_repo','')} |",
            f"| Engine | {proj.get('engine','')} |",
            f"| Target device | {esc(proj.get('target_device',''))} |",
            f"| ABI | {proj.get('abi','')} |",
            f"| Status | {proj.get('status','')} |",
            f"| Maintainer | {proj.get('maintainer','')} |",
            f"| Patches ref | {proj.get('patches_ref','')} |",
            "",
            "## Phases",
            "",
            "| Phase | Status |",
            "|---|---|",
        ]
        for p in sorted(proj.get("phases", {})):
            lines.append(f"| {p} | {proj['phases'][p]} |")
        lines.append("")
        lines.append("## Field notes (auto-synced)")
        lines.append("")
        if log:
            render_journey(lines, log)
        else:
            lines.append("_No field-notes log fetched yet; the next sync will fill this in._")
            lines.append("")
        lines.append("<!-- generated; do not hand-edit -->")
        with open(os.path.join(ROOT, "projects", slug, "README.md"), "w") as f:
            f.write("\n".join(lines).rstrip() + "\n")
        status_icon = {"done": "✅", "active": "🔵", "maintained": "🛡️",
                       "in-progress": "🔄", "planning": "⏳",
                       "pending": "⏳", "paused": "⏸️"}.get(proj.get("status"), "•")
        index.append(f"- {status_icon} **[{proj['name']}]({slug}/README.md)** — {esc(proj.get('description',''))} "
                     f"({proj.get('status','')}, {proj.get('abi','')})")
    index.append("")
    with open(os.path.join(ROOT, "projects", "README.md"), "w") as f:
        f.write("\n".join(index))
    print(f"generated {len(manifests)} project doc(s) + index")

if __name__ == "__main__":
    main()
