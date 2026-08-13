# 05 — GitHub free-tier operations (stay at $0, long-term)

## The limits that matter

- **Artifacts**: 500 MB total storage (public repos).
- **Cache**: 10 GB.
- **Retention**: artifacts default 90 days; set shorter (7–14 d) per job.
- **Scheduled workflows in public repos can be disabled after ~60 days without repository activity.** Any push/dispatch resets the window, but do NOT rely on schedule alone — provide `workflow_dispatch` + `repository_dispatch` as secondary triggers.

## The monthly maintenance workflow (what it does)

Runs `0 5 1 * *` + dispatch:
1. Delete artifacts older than 14 days (`gh api repos/{owner}/{repo}/actions/artifacts`).
2. Evict caches older than 14 days (`actions/caches`).
3. Trim workflow runs to newest 20 (`gh run list ... | head -n -20 | xargs gh api -X DELETE actions/runs/{id}`).
4. Writes a job summary.

Why it matters: keeping the repo inside the limits automatically means the pipeline "just works" forever without manual cleanup.

## Deletion hygiene tips

- `gh run list -L 100 --json databaseId,createdAt` then sort/trim, not `gh run delete` one-by-one for every run.
- Deleting old runs/artifacts is safe for the release path IF the release asset (GitHub Release) is a separate durable store, and SHA-256 checksums are kept with the release.
- Old `gh api -X DELETE .../runs/{id}` also removes failed/superseded builds that waste the 500 MB quota.

## Runner minutes

- arm64-only + Gradle caches + `fast=true` (no R8) cut build time dramatically (39 min → much less). Upstream check workflow never builds, so it is ~free.
- Public repos get free minutes on GitHub-hosted runners; keep heavy builds opt-in via dispatch, not on every push.
