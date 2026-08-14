---
name: project-intake
description: Classify an arbitrary source repo (language, framework, build system) and auto-draft the projects/<slug>/ scaffolding for a new special build in the playbook — manifest.yml (engine: geckoview | webview | native | other), roadmap.md (phases 0–10), workflow.md, and PROMPT.md. Use when starting a new special-build project, when asked to intake/onboard a repo into the playbook, or when unsure what engine a candidate repo actually uses. Never guesses: fields that cannot be inferred stay TODO, and repos that fit no engine are flagged for enum extension instead of being forced into a bucket.
---

# Project Intake

Auto-drafts a new `projects/<slug>/` entry for the playbook from an arbitrary
source repo: detect the stack, map it to the existing manifest `engine` enum,
and scaffold `manifest.yml` + `roadmap.md` + `workflow.md` + `PROMPT.md` for
human review. Same contract as the rest of the playbook: drafts are reviewed
and committed manually, never auto-merged.

## Self-update (run this first)

This skill is a live copy of `rajbhx/op7-special-build-playbook` →
`skills/project-intake/`. Refresh it in place at the start of a session
(or whenever knowledge seems stale) with the bundled updater:

```
bash /root/.shared-skills/project-intake/scripts/update_skill.sh
```

Generic form (any machine): run `scripts/update_skill.sh` from the skill
directory. Behavior:

- Cheap check first: one `git ls-remote` — a few seconds when up to date.
- On change: sparse fetch of the skill dir, validation, then an atomic swap
  with a timestamped backup (`project-intake.backup-<timestamp>`).
- Offline / rate-limited: keeps the current copy and warns — never breaks a
  session.
- Env overrides: `PLAYBOOK_REPO` (remote), `SKILL_ROOT` (install root),
  `EXTRA_SKILL_ROOTS` (space-separated extra roots to update in place).

## Usage

```
python3 scripts/intake.py --repo <url-or-path> --slug <slug> [--out <playbook-root>] [--dry-run]
```

- `--repo` — git URL or local checkout of the candidate source repo.
- `--slug` — `[a-z0-9-]+` folder name for the new project (must match the
  manifest `slug` field).
- `--out` — playbook root to write into (default: current directory; must
  contain `projects/` — a warning is printed otherwise).
- `--dry-run` — print the detection report + what would be written, write
  nothing.

Output is always a DRAFT: `status: planning`, uninferrable fields stay
literal `TODO` (never guessed), and every file carries a "review before
commit" banner. The user reviews and commits manually, same as everything
else in this repo.

## Never overwrite

- If `projects/<slug>/` does not exist → drafts go to `projects/<slug>/`.
- If it already exists → drafts go to `intake-drafts/<slug>/` (gitignored)
  and the tool diffs the draft against the existing tree so you can see
  exactly what would change. It never silently replaces files.

## Engine mapping (summary — details in references/detection-rules.md)

| Signal | Engine |
|---|---|
| `org.mozilla.geckoview` / `geckoview-omni` / `mozilla.components` / mozilla-central | `geckoview` |
| `android.webkit.WebView` (no GeckoView) | `webview` |
| Tauri / Electron / Capacitor (system webview wrapper) | `webview` |
| Flutter (`pubspec.yaml` + `flutter:`) | `native` (Flutter engine, not webview) |
| Rust `Cargo.toml` (no Tauri) / CMake / .NET / Swift | `native` |
| Node (no Electron) / Python / scripts | `other` |
| No clean fit | **flagged for review** — engine enum extension proposed, nothing written |

Never force a guess: if the repo fits no engine cleanly, `intake.py` prints
why, proposes an enum extension (e.g. adding `electron` to
`scripts/validate_manifests.py`), and exits without drafting.

## Output files (all drafts)

- `manifest.yml` — pre-filled with detected `engine` (+ `abi` when
  discoverable), `status: planning`, all phases `pending`; `name`,
  `description`, `repo`, `upstream_repo` (when unknown), `target_device`,
  `maintainer`, `field_notes.repo`, `patches_ref` stay `TODO`.
- `roadmap.md` — phases 0..10 mapped to the detected project type (a
  GeckoView fork's phase 0/1 is not a Flutter app's).
- `workflow.md` — the actual repeatable commands for this stack: build,
  test/lint, install-to-device (when applicable), benchmark approach (same
  intent as playbook `docs/07-on-device-benchmarking.md`, generated
  per-project, not copied).
- `PROMPT.md` — a short onboarding brief for whichever agent picks up this
  project next, scoped to just this project.

## Golden rules (shared with the playbook)

- Baseline before optimization; measure on the real device; never optimize
  on assumptions.
- Thin patch layer only; never fork the app source wholesale.
- One measured optimization per revision; benchmark before/after.
- Never publish an unvalidated build; never force-reset to upstream.
- Free infra only (GitHub Actions/Releases/caches).

## References (load on demand)

- `references/detection-rules.md` — full signal table, confidence rules,
  ABI discovery, edge cases (Electron/Tauri/Flutter/unknown)
- Playbook `docs/00-quickstart.md` — phases 0..10 and order of operations
- Playbook `AGENTS.md` — manifest schema + file ownership (drafts are
  hand-edited, i.e. reviewable; generated layers stay untouched)
