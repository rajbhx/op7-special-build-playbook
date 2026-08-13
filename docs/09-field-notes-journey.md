# 09 — Field notes: problems we actually hit and how we solved them

Chronological log from the Iceraven OP7 project. Reusable for any app.

## A. Build pipeline

| # | Problem | Root cause | Solution |
|---|---|---|---|
| A1 | `destination path 'upstream' already exists` | workflow cloned into `upstream/`, a tracked dir of the repo | clone into `mirror/` instead; keep clone dirs out of tracked paths |
| A2 | `removeUnusedEntriesOlderThan` write-only property crash | gradle-build-action **v3** cleanup incompatible with Gradle 9.5.1 | pin gradle-build-action **v2** (upstream-proven) |
| A3 | `APK not found` (first time) | hardcoded AGP output path; ABI selection changes output layout | `find`-based discovery, name-agnostic |
| A4 | `APK not found` (second time) | unsigned APKs named `*-forkRelease-unsigned.apk` (no signing config in forkRelease) | discovery handles `-unsigned`; sign step renames to `.apk` |
| A5 | AAPT `unexpected package id` | OP7 patch appends `.iceraven.op7` to app id | expect the patched id; derive at runtime from patches + defaultConfig |
| A6 | sign action "build-tools not found" | action read `ANDROID_HOME` (runner SDK), we pointed at `ANDROID_SDK_ROOT` (custom SDK) | compute `BUILD_TOOLS_VERSION` from `ANDROID_HOME` like upstream; read third-party action source before use |
| A7 | GitHub cache service outage (`400` / "services aren't available") | GitHub-side transient | treat cache misses as warnings, not failures; stable cache keys; next run restores |
| A8 | R8 OOM risk with `--parallel` on 2-core/7 GB runner | workers vs heap | tune `GRADLE_OPTS`, drop/limit `--max-workers`, keep release builds serial if flaky |
| A9 | `native-code` badging line missing | ABI selection ignored by some AGP versions | validation gates fail loudly; configure `splits.abi` explicitly |
| A10 | Glean bootstrap (Miniconda3) not idempotent | wrapper re-downloaded every build | make bootstrap idempotent; skip if already present |
| A11 | Feasibility: full build ~40 min on free runner | GeckoView AAR download + R8 + all ABIs | arm64-only split, Gradle/Rust/Maven caches, `fast=true` (skip R8) for validation, `--parallel` when stable |

## B. Release / signing / storage

| # | Problem | Root cause | Solution |
|---|---|---|---|
| B1 | Release asset became stale bytes | validation build overwrote release asset data | compare bytes; only update release asset from a validated `release=true` run |
| B2 | PKCS12 alias mismatch risk | keystore alias vs secret | document exact alias; validate at first release |
| B3 | Release tag immutability | GitHub tags are immutable | fix version/tag in the dispatch; never reuse a tag |
| B4 | APK commits sneaking into the repo | `git add -A` picked up 3×126 MB APKs in a gitignored dir (they were tracked before the ignore was added) | `git rm --cached`; verify `git ls-files` empty; keep binaries out of git history |
| B5 | Old artifacts/runs wasted the 500 MB quota | 90-day default retention | monthly maintenance workflow prunes >14 d artifacts/caches, keeps newest 20 runs |

## C. Device / install

| # | Problem | Root cause | Solution |
|---|---|---|---|
| C1 | "App not installed" (the big one) | APK flagged `android:testOnly=true` (Studio-injected build flag); Android 10 blocks UI installs of testOnly | remove injected flag; `splits.abi` arm64-only; CI badging gate rejects testOnly; verify `pm install -r` without `-t` |
| C2 | `pm install -r` from `/sdcard/Download` → 255 | opaque failure installing directly from FUSE path | copy to `/data/local/tmp` first, then `pm install -r` |
| C3 | App open but Shizuku not connected | Shizuku server stopped/wasn't started; battery optimization kills it | `shizuku whoami` must print `shell`; retry loops; user reopens Shizuku |
| C4 | Wrong activity launched once in scripted runs | environment: assistant app foreground; HOME keyevent ineffective | verify `mCurrentFocus`; use explicit component; validate `LaunchState`/Activity in logs |

## D. Measurement / transfer

| # | Problem | Root cause | Solution |
|---|---|---|---|
| D1 | `am start -W` → `TotalTime: 0` | activity still top-most; not a launch at all | HOME/background between runs; filter to `LaunchState: COLD`; warm-start needs adb |
| D2 | Captured files empty (gfxinfo 0 B) | Shizuku wrapper races: large remote output streams to tty, local pipe gets 0 bytes | stage output to on-device temp file; pull with `wc -c` size probe + retry until local size == remote size |
| D3 | Exit codes unreliable through Shizuku | wrapper mangles remote exit codes | verify by output content (pidof non-empty, "Complete" marker) |
| D4 | GitHub artifact downloads truncated (4+ aborts) | unreliable network | local `python3 -m http.server` loopback transfer; 131 MB in ~1.5 s; SHA-256 verify |
| D5 | `/sdcard` files from shell unreadable by app proot | FUSE permission model; `chmod` unsupported | transfer via app-visible storage or MediaStore; verify sizes |
| D6 | `bsh` stdout looks odd | returns JSON envelope `{"result":..,"output":..}`; no `readAllBytes()` (old Java) | parse JSON; read streams with BufferedReader loops |
| D7 | warm-start impossible in proot env | HOME no-op; `am finish` unavailable; BACK intercepted | record as pending; needs adb or HOME-capable session |

## E. CI quality

| # | Problem | Root cause | Solution |
|---|---|---|---|
| E1 | CI red after merge | shellcheck `SC2129` (individual `>>` redirects to summary) | group echos with `{ ...; } >> file` |
| E2 | `testOnly` gate missing | validation gap | badging step fails when `testOnly=true` appears |
| E3 | Scheduled workflow 60-day caveat | GitHub policy for public repos | daily check + dispatch + monthly maintenance reset the activity window; manual/repo-dispatch as secondary triggers |

## Recurring failure signature

If output is "sometimes there, sometimes not": it is almost always a transport
race, not the command. Fix by staging on-device + verifying size/content, then
retry. This pattern solved the most frustrating debugging hours.
