# Build pipeline (iceraven-op7)

## Workflows (.github/workflows/)
- `ci.yml` — PR/push validation (mirror upstream → patch → build → validate).
- `op7-build.yml` — manual dispatch: `-f abi=arm64-v8a -f release=false -f fast=true`. Always `fast=true` during patch iteration.
- `release.yml` — `release=true` builds; debug-signs with `DEBUG_*` secrets or release-signs with env-protected `OP7_RELEASE_*`.
- `upstream-sync.yml` / `check-upstream.yml` — scheduled upstream detection; lightweight check, full pipeline only when changed.
- `maintenance.yml` — monthly prune: artifacts/caches >14 days, keep newest 20 runs (GitHub free-tier limits).
- `security.yml` — dependency/secret scanning.

## Secrets
- Validation: `DEBUG_SIGNING_KEY`, `DEBUG_SIGNING_ALIAS`, `DEBUG_KEY_STORE_PASSWORD`, `DEBUG_KEY_PASSWORD`.
- Release (env-protected): `OP7_RELEASE_*`. Never commit keys; never expose to PRs from forks.

## Caching (free tier)
- `gradle-build-action` v2 — v3 is incompatible with Gradle 9.5.1 (crashes on cleanup).
- Keys include OS/arch/toolchain/deps; cache misses are warnings, not failures; never cache binaries that can go stale (APKs, AARs of upstream).

## Mandatory validation gates (release only when ALL pass)
source sync → patches apply → deps resolve → compile → tests → APK generated → structural validity (`aapt dump badging`: correct package id `org.mozilla.fenix.iceraven.op7`, NOT testOnly) → ABI arm64-v8a only → version metadata → signing → SHA-256 checksum.

## Versioning
`iceraven-<upstream-ver>-op7r<revision>`; `op7-revision.txt` in repo root; build metadata JSON records upstream commit, GV version, patch revision, run id.
