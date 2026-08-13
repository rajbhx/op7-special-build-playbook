# Iceraven OP7

> Auto-generated from `projects/iceraven-op7/manifest.yml` and the
> project's field-notes log. Do not hand-edit the journey section.

## Project

| Field | Value |
|---|---|
| Description | OnePlus 7 optimized Iceraven (GeckoView) distribution, arm64-v8a only |
| Build repo | https://github.com/rajbhx/iceraven-op7 |
| Upstream | https://github.com/fork-maintainers/iceraven-browser |
| Engine | geckoview |
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
| 7 | pending |
| 8 | pending |
| 9 | pending |

## Field notes (auto-synced)

### A. Build pipeline

| # | Problem | Root cause | Solution |
|---|---|---|---|
| A1 | destination path 'upstream' already exists | workflow cloned into 'upstream/', a tracked dir of this repo | clone into 'mirror/' instead; keep clone dirs out of tracked paths |
| A2 | removeUnusedEntriesOlderThan write-only property crash | gradle-build-action v3 cleanup incompatible with Gradle 9.5.1 | pin gradle-build-action v2 (upstream-proven) |
| A3 | APK not found (first time) | hardcoded AGP output path; ABI selection changes output layout | find-based discovery, name-agnostic |
| A4 | APK not found (second time) | unsigned APKs named '*-forkRelease-unsigned.apk' (no signing config) | discovery handles '-unsigned'; sign step renames to .apk |
| A5 | AAPT unexpected package id | OP7 patch appends '.iceraven.op7' to app id | expect the patched id; derive at runtime from patches + defaultConfig |
| A6 | sign action 'build-tools not found' | action read ANDROID_HOME (runner SDK), we used ANDROID_SDK_ROOT (custom SDK) | compute BUILD_TOOLS_VERSION from ANDROID_HOME like upstream; read third-party action source before use |
| A7 | GitHub cache service outage (400 / services unavailable) | GitHub-side transient | cache misses are warnings not failures; stable cache keys; next run restores |
| A8 | R8 OOM risk with --parallel on 2-core/7 GB runner | workers vs heap | tune GRADLE_OPTS, limit --max-workers, keep release builds serial if flaky |
| A9 | 'native-code' badging line missing | ABI selection ignored by some AGP versions | validation gates fail loudly; configure splits.abi explicitly |
| A10 | Glean bootstrap (Miniconda3) not idempotent | wrapper re-downloaded every build | make bootstrap idempotent; skip when already present |
| A11 | full build ~40 min on free runner | GeckoView AAR download + R8 + all ABIs | arm64-only split, Gradle/Rust/Maven caches, fast=true (no R8) for validation, --parallel when stable |

### B. Release, signing, storage

| # | Problem | Root cause | Solution |
|---|---|---|---|
| B1 | release asset became stale bytes | validation build overwrote release asset data | compare bytes; only update release asset from a validated release=true run |
| B2 | PKCS12 alias mismatch risk | keystore alias vs secret | document exact alias; validate at first release |
| B3 | release tag immutability | GitHub tags are immutable | fix version/tag in the dispatch; never reuse a tag |
| B4 | APK commits sneaking into the repo | git add -A picked up 3x126 MB APKs in a gitignored dir (tracked before ignore added) | git rm --cached; verify git ls-files empty; keep binaries out of git history |
| B5 | old artifacts/runs wasted the 500 MB quota | 90-day default retention | monthly maintenance workflow prunes >14 d artifacts/caches, keeps newest 20 runs |

### C. Device and install

| # | Problem | Root cause | Solution |
|---|---|---|---|
| C1 | App not installed | APK flagged android:testOnly=true (Studio-injected build flag); Android 10 blocks UI installs | remove injected flag; splits.abi arm64-only; CI badging gate rejects testOnly; verify pm install -r without -t |
| C2 | pm install -r from /sdcard/Download returns 255 | opaque failure installing directly from FUSE path | copy to /data/local/tmp first, then pm install -r |
| C3 | app open but Shizuku not connected | Shizuku server stopped or killed by battery optimization | shizuku whoami must print 'shell'; retry loops; user reopens Shizuku |
| C4 | wrong activity launched in scripted runs | assistant app foreground; HOME keyevent ineffective in proot env | verify mCurrentFocus; use explicit component; validate LaunchState/Activity in logs |

### D. Measurement and transfer

| # | Problem | Root cause | Solution |
|---|---|---|---|
| D1 | am start -W returns TotalTime 0 | activity still top-most; not a launch at all | background between runs; filter LaunchState: COLD; warm-start needs adb |
| D2 | captured files empty (gfxinfo 0 B) | Shizuku wrapper races: large remote output streams to tty, local pipe gets 0 bytes | stage output to on-device temp file; pull with wc -c size probe + retry until sizes match |
| D3 | exit codes unreliable through Shizuku | wrapper mangles remote exit codes | verify by output content (pidof empty, 'Complete' marker) |
| D4 | GitHub artifact downloads truncated (4+ aborts) | unreliable network | local python3 -m http.server loopback transfer; 131 MB in ~1.5 s; SHA-256 verify |
| D5 | /sdcard files from shell unreadable by app proot | FUSE permission model; chmod unsupported | transfer via app-visible storage or MediaStore; verify sizes |
| D6 | bsh stdout looks odd | returns JSON envelope {result,output}; no readAllBytes() (old Java) | parse JSON; read streams with BufferedReader loops |
| D7 | warm-start impossible in proot env | HOME no-op; am finish unavailable; BACK intercepted | record as pending; needs adb or HOME-capable session |

### E. CI quality

| # | Problem | Root cause | Solution |
|---|---|---|---|
| E1 | CI red after merge | shellcheck SC2129 (individual >> redirects to summary) | group echos with { ...; } >> file |
| E2 | testOnly gate missing | validation gap | badging step fails when testOnly=true appears |
| E3 | scheduled workflow 60-day caveat | GitHub policy for public repos | daily check + dispatch + monthly maintenance reset the activity window; manual/repo-dispatch secondary |

### Recurring failure signature

If output is "sometimes there, sometimes not": it is almost always a transport
race, not the command. Fix by staging on-device + verifying size/content, then
retry. This pattern solved the most frustrating debugging hours.

<!-- generated; do not hand-edit -->
