# 04 — GitHub Actions build blueprint (Android special build)

Proven in the iceraven-op7 repo. Structure:

```
.github/workflows/
  ci.yml            # cheap repo-layer validation on push/PR (actionlint + shellcheck + pin checks)
  op7-build.yml     # the full browser build: dispatch with inputs (upstream_commit, abi, release, fast, release_tag)
  upstream-check.yml# daily lightweight upstream detection (never builds)
  maintenance.yml   # monthly prune of artifacts/caches/runs (free-tier hygiene)
```

## Build job essentials

- **Inputs**: `upstream_commit` (or pinned), `abi=arm64-v8a`, `release=false|true`, `fast=true|false` (skip R8), `release_tag`, `patch_ref`.
- **Concurrency group** keyed on upstream commit so overlapping dispatches cancel.
- **Clone upstream into `mirror/`**, NOT into a tracked dir of your repo (avoids `destination path already exists` and keeps the tree clean).
- **Apply patch layer**: `patches/<project>/NNN-*.patch` via `git apply --3way`; any failure = stop, report, never force.
- **Discover the APK by glob**, never hardcode AGP output paths (`*-forkRelease-unsigned.apk` vs signed naming varies by ABI selection and signing config).
- **Badging gate**: package id, minSdk/targetSdk, `native-code: arm64-v8a`, `lib/<abi>/` present, NOT testOnly.
- **Signing**: `r0r0o/r0-paths-filter`-style actions exist upstream; pick actions pinned to upstream's proven versions (see gotchas — gradle-build-action v3 crashed on Gradle 9.5.1, v2 was stable).
- **Two artifacts**: validation (7-day retention) + signed APK (14-day); release builds only upload what's needed.

## Caching (free tier)

- Gradle + Android SDK + Rust/Cargo + Maven caches via `gradle/actions/setup-gradle` (v2) with keys that include OS, arch, toolchain, and source config hashes.
- Cache keys must never produce stale binaries; restore is best-effort (cache service outages are transient — treat misses as warnings, not failures).

## Immutable rules

- Release only from `release=true` + a protected `release` environment + `OP7_RELEASE_*` secrets guarded by presence checks.
- PRs from untrusted forks never see secrets.
- Never commit keystores/keys to git.
- End of build: job summary with source commit, upstream commit, patch status, cache hit/miss, test status, artifact status.
