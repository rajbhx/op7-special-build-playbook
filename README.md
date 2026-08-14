# OP7 Special-Build Playbook

[![CI](https://github.com/rajbhx/op7-special-build-playbook/actions/workflows/ci.yml/badge.svg)](https://github.com/rajbhx/op7-special-build-playbook/actions/workflows/ci.yml)

Field notes from building a device-specific Android browser distribution
(Iceraven OP7 for the OnePlus 7) — problems hit, root causes, and the solutions
that stuck. Built to be reused for other apps and other special builds.

- Working implementation: https://github.com/rajbhx/iceraven-op7 (public)
- Docs folder in that repo mirrors the live workflow/scripts/patches.

## How to use this

0. **Agents**: connect with the `op7-special-build` Codex skill.
   - New machine/agent — one command:
     `bash scripts/install_skill.sh` (installs into `$CODEX_HOME/skills` or
     `~/.codex/skills`, records the source commit, self-verifies).
   - Already installed — refresh at session start:
     `bash /root/.shared-skills/op7-special-build/scripts/update_skill.sh`
     (one `git ls-remote` when up to date; sparse fetch + atomic backup on
     change; offline-safe).
   - No skill support — search first, read only what matches:
     `python3 scripts/lookup.py <problem words>` (or grep `notes/*/INDEX.md`).
     Full-detail files: `notes/<slug>/entries/<id>.md`. See `AGENTS.md`.

## Docs

> Two docs intentionally share the `00` prefix: `00-master-spec.md` is the
> canonical engineering contract (spec + operating rules, kept verbatim), while
> `00-quickstart.md` is the enforced order of operations. Both are hand-edited
> entry points, so neither is renumbered.

| Doc | What it covers |
|---|---|
| `00-master-spec.md` | the full engineering contract (ROLE, 35 requirements, success criteria, user operating rules) |
| `00-quickstart.md` | order of operations + agent connect/refresh |
| `01-op7-device-facts.md` | verified OnePlus 7 hardware facts |
| `02-device-access-and-transfer.md` | reaching the device without USB (Shizuku, no adb) |
| `03-apk-not-installed.md` | install failures (testOnly, ABI, signing) |
| `04-build-pipeline-blueprint.md` | GitHub Actions build pipeline + auto-release flow |
| `05-github-free-tier-operations.md` | staying inside GitHub's free limits |
| `06-upstream-automation.md` | upstream sync/conflict handling |
| `07-on-device-benchmarking.md` | measurement methodology |
| `08-versioning-reproducibility.md` | version identity + reproducible builds |
| `09-field-notes-journey.md` | human-readable journey (auto-synced) |
| `10-porting-playbook.md` | porting this to another app, step by step |
| `11-amoled-theming.md` | pure-black AMOLED theming + brand accent for Fenix forks |

## Projects

See the auto-generated index: `projects/README.md`.
Each project's problems->solutions log is fetched automatically from its own
repo by the `Playbook Sync` workflow (every 6h + manual + `repository_dispatch`
type `field-notes-sync`), so the playbook grows on its own as you build more
special editions.

Everything here is free-infrastructure only (GitHub Actions/Releases), no paid CI.

## Golden rules that survived contact

- Baseline first. Measure before you optimize. Never optimize on assumptions.
- Keep custom changes in a thin patch layer, never fork the app's source.
- One measurable optimization per revision, with before/after numbers.
- Never publish an unvalidated build. Never force-reset to upstream.
- Never commit signing keys or large binaries to git (git add -A will bite you).
