# Rain OP7

> Auto-generated from `projects/rain-op7/manifest.yml` and the
> project's field-notes log. Do not hand-edit the journey section.

## Project

| Field | Value |
|---|---|
| Description | OnePlus 7 edition of the ra1ncord Discord client mod (rainManager APK + rain bundle) |
| Build repo | https://github.com/rajbhx/rain-op7 |
| Upstream | https://github.com/ra1ncord/rainManager |
| Engine | native |
| Target device | OnePlus 7 (GM1901) |
| ABI | arm64-v8a |
| Status | active |
| Maintainer | rajbhx |
| Patches ref | patches/op7/ |

## Phases

| Phase | Status |
|---|---|
| 0 | done |
| 1 | done |
| 10 | pending |
| 2 | in-progress |
| 3 | done |
| 4 | done |
| 5 | planning |
| 6 | pending |
| 7 | in-progress |
| 8 | pending |
| 9 | pending |

## Field notes (auto-synced)

### A. Repository discovery & architecture

| # | Problem | Root cause | Solution |
|---|---|---|---|
| RAIN1 | which ra1ncord repos are actually needed for the Android build was ambiguous | org has rain (TS), rainManager (Kotlin), rainXposed (Kotlin), RainTweak (C++) | mapped ecosystem - deliverable APK = rainManager; bundle = rain; rainXposed runtime-fetched; RainTweak iOS-only excluded |

### B. Build, validation & ABI

| # | Problem | Root cause | Solution |
|---|---|---|---|
| RAIN2 | rainManager ships no native-code entries in badging (lspatch .so live in assets) | lspatch runtime is injected into the patched Discord APK, not used by the manager itself | validation gate for the manager checks package/SDK/testOnly only; patched-output ABI is inherited from Discord (arm64-v8a on OP7) |

### C. CI infrastructure

| # | Problem | Root cause | Solution |
|---|---|---|---|
| RAIN3 | upstream rain CI runs on Codeberg Forgejo, not GitHub | canonical repo is codeberg raincord; GitHub ra1ncord is a mirror | reuse the exact build command (bun run build --release-branch=main --build-bytecode) on GitHub Actions; pin GitHub mirror commits |

<!-- generated; do not hand-edit -->
