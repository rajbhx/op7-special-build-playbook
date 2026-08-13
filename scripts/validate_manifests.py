#!/usr/bin/env python3
"""Validate all projects/*/manifest.yml entries. No network. Exit 1 on error.

Run in CI (playbook repo) so agents get fast feedback when adding a project.
"""
import glob
import os
import re
import sys
import yaml

REQUIRED = ["slug", "name", "description", "repo", "upstream_repo", "engine",
            "target_device", "abi", "status", "maintainer", "field_notes"]
FIELD_NOTES_REQUIRED = ["repo", "path"]
PHASES = [str(i) for i in range(11)]
STATUS = {"planning", "active", "maintained", "paused"}
ENGINES = {"geckoview", "webview", "native", "other"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    errors = []
    seen = set()
    files = sorted(glob.glob(os.path.join(root, "projects", "*", "manifest.yml")))
    if not files:
        errors.append("no projects/*/manifest.yml found")
    for path in files:
        slug_dir = os.path.basename(os.path.dirname(path))
        if slug_dir == "_template":
            continue
        with open(path) as f:
            data = yaml.safe_load(f)
        proj = (data or {}).get("project")
        if not isinstance(proj, dict):
            errors.append(f"{path}: missing 'project:' mapping"); continue
        for field in REQUIRED:
            if field not in proj:
                errors.append(f"{path}: missing required field '{field}'")
        slug = proj.get("slug")
        if slug in seen:
            errors.append(f"{path}: duplicate slug '{slug}'")
        seen.add(slug)
        if slug != slug_dir:
            errors.append(f"{path}: slug '{slug}' != folder name '{slug_dir}'")
        if slug and not SLUG_RE.match(slug):
            errors.append(f"{path}: slug '{slug}' must match {SLUG_RE.pattern}")
        if proj.get("status") not in STATUS:
            errors.append(f"{path}: status '{proj.get('status')}' not in {sorted(STATUS)}")
        if proj.get("engine") not in ENGINES:
            errors.append(f"{path}: engine '{proj.get('engine')}' not in {sorted(ENGINES)}")
        fn = proj.get("field_notes")
        if isinstance(fn, dict):
            for field in FIELD_NOTES_REQUIRED:
                if not fn.get(field):
                    errors.append(f"{path}: field_notes missing '{field}'")
        phases = proj.get("phases", {})
        for p in phases:
            if p not in PHASES:
                errors.append(f"{path}: unknown phase key '{p}'")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {len([f for f in files if 'template' not in f])} project manifest(s) valid")

if __name__ == "__main__":
    main()
