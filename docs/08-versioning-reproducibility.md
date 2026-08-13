# 08 — Versioning, signing, reproducibility

## Versioning

- Never invent a parallel versioning system; extend the app's existing scheme.
- Every build identifies: app version + upstream commit + OP7 (device) revision + workflow run.
- Example: `op7-2.46.0-r<rev>` tag, `versionName=iceraven-2.46.0-op7r2`, `versionCode` kept from upstream + suffixing as needed.

## Signing

- CI/dev: a debug keystore kept ONLY in GitHub secrets (`DEBUG_SIGNING_KEY`, `DEBUG_ALIAS`, `DEBUG_KEY_STORE_PASSWORD`, `DEBUG_KEY_PASSWORD`).
- Public releases: dedicated release key in a protected `release` environment (`OP7_RELEASE_KEYSTORE_BASE64`, `OP7_RELEASE_KEYSTORE_PASSWORD`, `OP7_RELEASE_KEY_ALIAS`, `OP7_RELEASE_KEY_PASSWORD`), presence-guarded; never visible to PRs/forks.
- Back up the release keystore offline; losing it = cannot update a published app.

## Reproducibility

- `docs/reproducible-build.md` should let any developer reproduce an exact release from: repo commit, upstream commit, patch revision, workflow revision, build config (Gradle/JDK/SDK versions).
- Publish per release: APK + SHA256SUMS.txt + build metadata (upstream commit, version, patch revision, ABI, Android target, run id).

## Storage model

- GitHub Releases = durable artifact store (separate from 90-day action artifacts).
- Action artifacts = short-lived pipeline inputs; monthly maintenance prunes them.
