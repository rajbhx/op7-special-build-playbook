# OP7 Special-Build Playbook

Field notes from building a device-specific Android browser distribution
(Iceraven OP7 for the OnePlus 7) — problems hit, root causes, and the solutions
that stuck. Built to be reused for other apps and other special builds.

Working implementation: https://github.com/rajbhx/iceraven-op7 (public)
Docs folder in that repo mirrors the live workflow/scripts/patches.

## How to use this

0. **Agents**: if your environment supports skills, load the `op7-special-build`
   skill (in `skills/op7-special-build/`); otherwise search first, read only what matches —
   `python3 scripts/lookup.py <problem words>` (or grep `notes/*/INDEX.md`).
   Full-detail files: `notes/<slug>/entries/<id>.md`. See `AGENTS.md`.
1. Read `docs/00-quickstart.md` for the order of operations (baseline before optimization).
2. If your build fails to install: `docs/03-apk-not-installed.md`.
3. If you are stuck reaching the device without USB: `docs/02-device-access-and-transfer.md`.
4. If you are building on GitHub Actions: `docs/04-build-pipeline-blueprint.md` + `docs/05-github-free-tier-operations.md`.
5. For the whole story of a project: `projects/<slug>/README.md` (auto-synced journey).
6. To add a NEW project/app: copy `projects/_template/`, fill the manifest, see `AGENTS.md`.

## Projects

See the auto-generated index: `projects/README.md`.
Each project's problems->solutions log is fetched automatically from its own
repo by the `Playbook Sync` workflow (weekly + manual + `repository_dispatch`
type `field-notes-sync`), so the playbook grows on its own as you build more
special editions.

Everything here is free-infrastructure only (GitHub Actions/Releases), no paid CI.

## Golden rules that survived contact

- Baseline first. Measure before you optimize. Never optimize on assumptions.
- Keep custom changes in a thin patch layer, never fork the app's source.
- One measurable optimization per revision, with before/after numbers.
- Never publish an unvalidated build. Never force-reset to upstream.
- Never commit signing keys or large binaries to git (git add -A will bite you).
