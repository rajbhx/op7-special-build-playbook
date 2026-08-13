# 09 — Field notes: problems we actually hit and how we solved them

> Auto-generated from `docs/field-notes/log.yml` in the `iceraven-op7` build repo
> by `.github/workflows/playbook-sync.yml` -> `scripts/build_notes.py`. Do not hand-edit.
> For agent use, search the compact layer: `scripts/lookup.py <words>` or
> grep `notes/iceraven-op7/INDEX.md`.

Chronological log from the field. Reusable for any app.

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
| D7 | warm-start impossible in proot env | HOME no-op; am finish and am task move-task-to-back unknown on this Android build; BACK intercepted | record as pending; needs adb or HOME-capable session |
| D8 | dumpsys meminfo/gfxinfo returned 'No process found' or empty | app process was force-stopped by the preceding cold-start loop | launch the app and let it render BEFORE capturing mem/gfx (cmd_mem launches; run gfx after mem) |
| D9 | large dumpsys outputs (>40 KB) only partially pull through Shizuku | wrapper stdout race gets worse with payload size; 400 KB batterystats truncated at 82% after 15 retries | accept partial captures and label them, or use chunked pulls / adb / MediaStore for full captures |

### E. CI quality

| # | Problem | Root cause | Solution |
|---|---|---|---|
| E1 | CI red after merge | shellcheck SC2129 (individual >> redirects to summary) | group echos with { ...; } >> file |
| E2 | testOnly gate missing | validation gap | badging step fails when testOnly=true appears |
| E3 | scheduled workflow 60-day caveat | GitHub policy for public repos | daily check + dispatch + monthly maintenance reset the activity window; manual/repo-dispatch secondary |
| E4 | r3 build failed at app:compileForkReleaseKotlin | missing import for DeviceCapabilities in HomeActivity; PackageManager.getSystemFeatureInfo/FEATURE_OPENGLES_* unresolved in this module (used deviceConfigurationInfo.reqGlEsVersion instead) | review imports before shipping a patch; prefer deviceConfigurationInfo for GLES version; ALWAYS re-stage BOTH files before regenerating a patch (git reset unstaged them and the regenerated patch silently lost the HomeActivity hunks) |
| E5 | r3 build failed at app:compileForkReleaseKotlin (Unresolved references) | missing DeviceCapabilities import in HomeActivity; PackageManager feature APIs unresolved in this module | added import; use deviceConfigurationInfo.reqGlEsVersion for GLES; review imports/APIs before dispatching |
| E6 | full 40-min build wasted on a compile error | dispatched full build before local review of the Kotlin patch | use fast=true validation builds during patch iteration (compile-level proof, cheap); full R8 only when ready |
| E7 | regenerated patch silently lost hunks after git reset | git reset unstaged files; regenerated diff from only one staged file | always re-stage ALL touched files before regenerating a patch; verify patch touches expected files (grep '^diff --git') |

### F. UI / perceived performance

| # | Problem | Root cause | Solution |
|---|---|---|---|
| F1 | visible color jump between splash and home screen on launch | hard-coded splash brand color (#FCF3EE / #210340) differs from home surface (#F7F6FB / #1D1B1F) | splash background references @color/fx_mobile_surface (patch 004) — seamless iOS-style launch, cosmetic only |

### G. Playbook & knowledge

| # | Problem | Root cause | Solution |
|---|---|---|---|
| G1 | full journey tables (docs/09, projects/*/README.md) cost agents too many tokens | every entry rendered in one big markdown table; an agent must read all of it to find one answer | notes/ layer — INDEX.md keyword->ids map (grep-able, ~150 lines), one entries/<id>.md per problem, lookup.py ranked search; agents read only the matching entry |
| G2 | keyword auto-extraction produced a noisy index (478 lines of '1.5', '2-core', 'add') | naive tokenization of problem+cause+solution text | curated INDEX from problem text + explicit tags only; full text kept in index.json for ranked lookup.py matching; stopwords + prefix-collapse |
| G3 | conversation digests lived only in the build repo, not the playbook | playbook sync fetched only log.yml | sync also lists docs/field-notes/sessions and fetches each *.md (skip _template) into _logs/sessions/<slug>/; SESSIONS.md generated with summaries |
| G4 | optional tags would be stripped by session_to_notes re-render | canonical renderer wrote only id/problem/cause/solution | renderer + digest parser now carry tags: [...] through |

### Recurring failure signature

If output is "sometimes there, sometimes not": it is almost always a transport
race, not the command. Fix by staging on-device + verifying size/content, then
retry. This pattern solved the most frustrating debugging hours.

<!-- generated; do not hand-edit -->
