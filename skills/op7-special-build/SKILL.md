---
name: op7-special-build
description: Field-proven workflows and lessons for device-specific Android app distributions — currently Iceraven/GeckoView for the OnePlus 7 (Snapdragon 855, arm64-v8a), reusable for other special builds. Use when working on the iceraven-op7 build repo or the op7-special-build-playbook, doing baseline/performance/optimization phases, patching GeckoView/Fenix, running GitHub Actions builds of Iceraven, validating/installing the APK on a real device, or extending the auto-synced field-notes knowledge loop.
---

# OP7 Special-Build

Auto-maintained knowledge base + workflows for building device-specific Android app distributions (Iceraven + GeckoView on OnePlus 7), designed to be reused for other apps and understood by other AI agents.

## Repos

- Build: `rajbhx/iceraven-op7` — Iceraven (Fenix fork); OP7 changes live only in `patches/op7/NNN-*.patch` (apply in order 001→006; latest r7 = pure-black AMOLED + OnePlus red accent); revision in `op7-revision.txt`; APK version `iceraven-<upstream-ver>-op7r<rev>`; ABI arm64-v8a only.
- Playbook: `rajbhx/op7-special-build-playbook` — searchable knowledge base, auto-synced from the build repo's `docs/field-notes/log.yml` + session digests.

## Search first (never re-derive)

1. In a playbook clone: `python3 scripts/lookup.py <problem words>` (or `--id <ID>`, `--sessions`, `--tags`). Grep fallback: `notes/*/INDEX.md`.
2. Not cloned: `gh repo clone rajbhx/op7-special-build-playbook` (it is small) and run the same commands.
3. If a solution exists, read only `notes/<slug>/entries/<id>.md` — that is the whole answer.
4. If truly new: solve, then record it (see "Recording lessons") so the next agent finds it.

## Golden rules (hard constraints)

- Baseline before optimization; measure on the real device; label data "contended" when the device was in use. Never optimize on assumptions.
- Thin patch layer only; never fork the app source; never replace GeckoView with WebView.
- One measured optimization per revision; benchmark before/after; revert on regression.
- Never publish an unvalidated build; upstream conflicts stop the pipeline; never force-reset to upstream.
- Preserve Gecko security (sandboxing, site isolation, HTTPS). Never trade security for benchmarks.
- Free infra only (GitHub Actions/Releases/caches); no paid CI, storage, or services.

## Phase order (0–10, enforced)

0 audit → 1 unmodified build → 2 baseline measurements → 3 CI reliability → 4 upstream auto-sync → 5 capability detection → 6 profiling → 7 first measured optimization → 8 benchmark/regression system → 9 automated release → 10 long-term maintenance.

## Costliest field gotchas

- "App not installed" on Android 10 = `android:testOnly=true` (Studio-injected flag). Remove injected flags; validate with `aapt dump badging` (reject testOnly) and `pm install -r` without `-t`.
- Package only `arm64-v8a` (`splits.abi`); packaging all 3 ABIs triples time + artifact size.
- Patch iteration: always dispatch CI with `-f fast=true` (no R8, ~13 min). Full release build ~40 min — use only when ready.
- Regenerating a patch after `git reset` silently loses hunks: re-`git add` ALL touched files before `git diff --cached`, then grep the patch for expected `diff --git` lines and imports.
- Shizuku transport quirks: stage output on-device + verify size before pulling; trust content, not exit codes; `>40 KB` dumpsys output truncates.
- Warm-start timing is impossible without adb; record cold-start only, labeled.

## Recording lessons (keeps the playbook self-updating)

1. Write `docs/field-notes/sessions/<date>-<topic>.md` (see `_template.md`): `**P** problem` / `cause:` / `solution:` / `section:` / optional `tags:`.
2. Run `python3 automation/op7/session_to_notes.py <digest>` → appends to `docs/field-notes/log.yml` (dedupes, auto-ids, preserves tags).
3. Run `python3 automation/op7/conversation_to_notes.py` → archives the useful typed knowledge (RULE/DECISION/REQUEST/GOTCHA/GOAL) from the local Codex session into `docs/field-notes/conversations/` (local-only tool; no raw transcripts, trimmed to 300 chars per entry).
4. Commit + push. Playbook sync (every 6h + manual + `repository_dispatch` type `field-notes-sync`) regenerates the notes layer automatically.

## References (load on demand)

- `references/master-spec.md` — the full user engineering specification (ROLE, 35 requirements, success criteria) + user operating rules; canonical copy in playbook `docs/00-master-spec.md`
- `references/pipeline.md` — CI workflows, secrets, caches, validation gates, release flow, versioning
- `references/device-facts.md` — verified OP7 hardware facts + how to verify on-device (Phase 5)
- `references/playbook.md` — knowledge loop, lookup usage, adding a new app/project
- `references/expo-rn-porting.md` — porting an Expo/RN app (DeepDenoiser pattern): no-EAS prebuild, lockfile pinning, ONNX NDK combo, badging gate
- `references/rain-ecosystem.md` — ra1ncord org map: rainManager APK + rain bundle, lspatch assets, Codeberg mirror
- `references/field-notes-sync.md` — canonical log schema, tags rules, journey selection, new-project checklist
