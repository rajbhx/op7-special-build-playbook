# OP7 Special-Build Playbook

Field notes from building a device-specific Android browser distribution
(Iceraven OP7 for the OnePlus 7) — problems hit, root causes, and the solutions
that stuck. Built to be reused for other apps and other special builds.

Working implementation: https://github.com/rajbhx/iceraven-op7 (public)
Docs folder in that repo mirrors the live workflow/scripts/patches.

## How to use this

1. Read `docs/00-quickstart.md` for the order of operations (baseline before optimization).
2. If your build fails to install: `docs/03-apk-not-installed.md`.
3. If you are stuck reaching the device without USB: `docs/02-device-access-and-transfer.md`.
4. If you are building on GitHub Actions: `docs/04-build-pipeline-blueprint.md` + `docs/05-github-free-tier-operations.md`.
5. If you want the whole story: `docs/09-field-notes-journey.md` (chronological problem log).

Everything here is free-infrastructure only (GitHub Actions/Releases), no paid CI.

## Golden rules that survived contact

- Baseline first. Measure before you optimize. Never optimize on assumptions.
- Keep custom changes in a thin patch layer, never fork the app's source.
- One measurable optimization per revision, with before/after numbers.
- Never publish an unvalidated build. Never force-reset to upstream.
- Never commit signing keys or large binaries to git (git add -A will bite you).
