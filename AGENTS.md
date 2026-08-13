# AGENTS.md — for AI agents (and humans) working in this repo

This repo is the **OP7 Special-Build Playbook**: a growing, machine-readable
knowledge base of problems+solutions for building device-specific Android app
builds (currently for the OnePlus 7). Every special-build project gets a
folder under `projects/`. Content is auto-synced from each project's own
field-notes log — agents do NOT hand-edit generated files.

## TL;DR for a new project

1. `cp -r projects/_template projects/<your-slug>`
2. Fill in `projects/<your-slug>/manifest.yml` (see schema below).
3. In the app's build repo, add `docs/field-notes/log.yml` (same YAML shape as
   `rajbhx/iceraven-op7/docs/field-notes/log.yml`).
4. Commit + push. The `Playbook Sync` workflow (weekly + manual +
   `repository_dispatch` type `field-notes-sync`) fetches the log and
   regenerates `projects/<slug>/README.md` + `projects/README.md`.
5. CI (`ci.yml`) validates your manifest on push/PR — fix errors before merging.

## When you solve a NEW problem in a project

- Append an entry to that project's `docs/field-notes/log.yml` (source repo),
  NOT to generated files here. Keep each field one line, short, factual.
- Entry schema per section: `id` (unique), `problem`, `cause`, `solution`.
- Optionally bump `recurring_signature` only when the pattern is genuinely new.

## Manifest schema (projects/<slug>/manifest.yml)

```yaml
project:
  slug: <folder-name-match>        # [a-z0-9-]+, must equal the folder name
  name: "Human name"
  description: "One line"
  repo: https://github.com/owner/slug
  upstream_repo: https://github.com/owner/upstream
  engine: geckoview | webview | native | other
  target_device: "OnePlus 7 (GM1901)"
  abi: arm64-v8a
  status: planning | active | maintained | paused
  maintainer: <gh-username>
  field_notes:
    repo: owner/slug               # public repo, gh api readable
    path: docs/field-notes/log.yml
  phases:                          # keys 0..10 per docs/00-quickstart.md
    "0": done
    ...
  patches_ref: patches/op7/
```

Validate locally: `python3 scripts/validate_manifests.py`.
Regenerate docs locally: `python3 scripts/generate_project_docs.py _logs/`
(after placing `_logs/<slug>.yml`, gitignored).

## File ownership

- Hand-edited: `AGENTS.md`, `README.md`, `projects/_template/`, `scripts/`,
  `.github/workflows/`, static `docs/` (except `docs/09*` which is generated).
- Generated, do NOT hand-edit: `projects/*/README.md`, `projects/README.md`.

## Golden rules (from the field)

- Baseline before optimization; never optimize on assumptions.
- Thin patch layer, never fork the app source.
- One measured optimization per revision; keep/revert on data.
- Never publish an unvalidated build; conflicts stop the pipeline.
- Never commit signing keys or large binaries (`git add -A` bites).
