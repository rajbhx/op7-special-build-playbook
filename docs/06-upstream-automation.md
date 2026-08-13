# 06 — Upstream sync that stays safe forever

Desired loop: detect → synch → patch → build → validate → release or report.

## Detection (cheap daily)

- Pin the upstream commit in a file (`upstream/commit.txt`).
- Daily workflow ONLY compares pinned vs upstream HEAD (no build). On change:
  1. open/update a "sync available" issue,
  2. dispatch the build with the new commit,
  3. summary.
- Never force-reset the repo to upstream; never drop local patches.

## Patch layer

- Keep all custom changes as `patches/<project>/NNN-description.patch` applied in order on top of the exact upstream commit.
- Every patch documents: problem, root cause, affected layer, implementation, expected benefit, benchmark, regression risk, upstream relationship.
- Patch applies with `git apply --3way`; a conflict stops publishing and opens an issue with: upstream commit, failing patch, conflicting files, last known-good release, suggested maintenance area.

## Revision/version scheme

- Extension, not replacement: `Iceraven version + upstream commit + OP7 revision` → e.g. `iceraven-2.46.0-op7r2`; revision counter in `op7-revision.txt`.
- Every release ships metadata: browser base version, upstream commit, patch revision, target ABI, Android target, GitHub run id, SHA-256.

## Safety invariant

- A release is valid only if: sync ok → patches ok → deps resolve → compile ok → tests pass → APK exists → badging ok → ABI ok → signing ok → checksum ok. Any gate fails → NO release, report instead.
- A working release is never replaced by an unvalidated build.
