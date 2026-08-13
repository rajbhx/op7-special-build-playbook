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
| C5 | am start with HomeActivity failed (Error type 3: activity does not exist) | launcher activity is the Fenix delegate `.App`, and the package id is io.github.forkmaintainers.iceraven.op7 (not org.mozilla.fenix.iceraven.op7) | resolve the launcher with `cmd package resolve-activity --brief -c android.intent.category.LAUNCHER <pkg>` before launching |
| C6 | user asked to undo bulk per-user uninstalls on a daily-driver phone | cleanup removed 12 already-disabled packages via pm uninstall --user 0 without asking first | restore exactly via `pm install-existing --user 0 <pkg>` then `pm disable-user --user 0 <pkg>`; verify with `pm list packages -d` matches the original list. Rule: on a daily-driver, present a candidate list and get a go-ahead before uninstalling packages; files/app-data need explicit confirmation too |

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
| D10 | proot files invisible to the real device shell (shizuku) | proot runs inside the app (gptos.intelligence.assistant); its /storage/emulated/0 is an app-private bind, not the real /sdcard | proot shares the device network, so serve the APK with a persistent loopback HTTP server (setsid nohup python3 -m http.server) and pull with curl on the real shell to /sdcard/Download/op7/; verify size; copy to /data/local/tmp then pm install -r |
| D11 | verify GeckoView uses hardware video decoding before touching media prefs | hardware decoders exist (Phase 5) but usage was unverified; changing prefs on assumptions is banned by the golden rule | media_probe.sh — force-stop, clear logcat, open a direct 1080p clip in Iceraven, sample top every 4s, dump logcat + dumpsys media.player; GeckoView's HardwareCodecCapability log names the selected decoder |
| D12 | summary CPU parse showed a fake 1034% spike in the probe | naive grep of leading digits grabbed the wrong column from top output | report peak from raw per-process samples; verify against cpu-all.txt before trusting a number |
| D13 | "3/6/10 tabs" memory captures were invalid — no new tabs were actually opened | repeated `am start -a VIEW -d <url>` on an already-foreground Fenix reuses the existing tab/task instead of creating new tabs; user confirmed no new tabs appeared | validate tab creation before measuring (uiautomator dump + user observation); VIEW-intent counts are not tab counts. Correct path: user opens tabs manually, or tap the real "New tab" toolbar node (from the Iceraven a11y dump) then drive the awesome bar |
| D14 | a11y dumps can show the WRONG app — the gptos assistant overlay, not the browser | the assistant host app renders its own floating UI on top; `uiautomator dump` captured that package's nodes | grep the dump for package="...iceraven..." and confirm mCurrentFocus before trusting coordinates/taps |
| D15 | needed real per-tab memory data but VIEW intents cannot create tabs in a foreground Fenix | repeated VIEW intents reuse the current tab (see D13); UI automation is blocked by the host app overlay (D14) | collaborative measurement — user opens 3/6/10 tabs by hand, `baseline_capture.sh state <n>` captures meminfo + processes as-is without force-stop |
| D16 | browser restarted between captures, changing the main pid and invalidating one sample | app instance churn mid-test (no crash logged); transient | use only settled states; verify pid + process set consistency before trusting a capture; retry truncated meminfo captures (146-byte truncation seen once) |
| D17 | "Remote debugging via USB" enabled but port 6000 not listening | GeckoView's remote debugger listens on a Unix abstract socket (io.github.forkmaintainers.iceraven.op7/firefox-debugger-socket), not TCP; adb forward is the normal bridge | verified via logcat `GeckoViewRemoteDebugger: listening on .../firefox-debugger-socket` |
| D18 | cannot reach the abstract socket without adb | SELinux denies the proot app domain (EACCES on connect); shell toybox nc has no -U; user declined adb authorization | accept the constraint — devtools measurement channel is unavailable on this setup; keep Shizuku dumpsys/top/logcat as the measurement stack |
| D19 | C1 'verified' was wrong — codec enumeration is not playback | r5 probe logged HardwareCodecCapability decoder selection + low CPU, but the probe clip URLs were 404, so no MediaCodec session ever ran; 'verified' was inferred, not observed | prove playback three ways: (1) fixture page beacons currentTime to a local HTTP server every 2 s (time-series must advance), (2) logcat must show a live MediaCodec session (OMX.qcom.video.decoder.*, component_init success, surface generation set) in our media pid, (3) user confirms video visible on screen |
| D20 | muted video never plays when tab goes background; decoder deinit on backgrounding | Gecko pauses muted background media (correct energy behavior); audible media keeps playing with decoder alive | for background-capable media tests: let the page unmute+play on a user tap (autoplay policy), then capture dumpsys/logcat from the agent side while user keeps chatting |
| D21 | VIEW intent on already-running Fenix task does not deliver the URL | am start -n on a foreground activity logs 'Activity not started' and only brings the task forward; new tab was never fetched (background tabs don't fetch until foregrounded) | cold-start reliably: am force-stop, then am start with the intent; or let the chooser resolve (no -n); drive navigation by tapping the URL bar + input text + keyevent 66 |
| D22 | alias URL http://127.0.0.1:8790/s rendered a blank page in Iceraven | the alias file 's' has no extension; python http.server serves it as application/octet-stream, and Gecko refuses to render a binary blob as HTML — page fetches 200 but shows nothing, JS never runs | always give fixture files a .html extension (or set MIME) — check Content-Type before relying on a local fixture; blank page + 200 = wrong MIME, not a browser bug |
| D23 | dumpsys gfxinfo <pkg> framestats showed 0 frames while the page was actively scrolling | gfxinfo measures only the main process; WebRender content renders in :tab_* and :gpu processes, so page frames never appear in the package's gfxinfo | measure compositor-level smoothness with dumpsys SurfaceFlinger --latency '<pkg>/<activity>#0' (line 1 = refresh ns, rows = desired/actual/ready); only judge deltas during continuous motion (idle gaps are not jank) |
| D24 | intent-opened URL tab never ran JS (no beacons) and showed blank/frozen | cold start with VIEW intent restores the old session in front and adds the URL tab in the background; background tabs suspend JS timers/rAF until foregrounded | foreground-only web tests: have the user paste the URL in the address bar (works reliably), or use the chooser route; don't expect the intent tab to run until it is the active tab |
| D25 | SurfaceFlinger --latency on ...HomeActivity#0 gave sparse frames (11) and fake jank while the page clearly scrolled | the #0 layer is the activity/chrome surface; GeckoView web content composites into the child SurfaceView layer, which only exists while the browser is visible | capture dumpsys SurfaceFlinger --latency with the SurfaceView layer name from --list (SurfaceView - <pkg>/<activity>#0); verify the surface is active (many frames) before trusting jank numbers; gfxinfo <pkg> = chrome only |
| D26 | am start -W failed with Binder 'Failed transaction (2147483646)' and HOT launches during cold-start re-measurement | rapid force-stop + start cycles under system contention (daily driver in use) hit Binder transaction failures; force-stop needs settle time or the old process survives | measure cold start as single commands: force-stop, sleep 3, verify no pid, then am start -W; confirm LaunchState: COLD per run; label contended samples honestly |
| D27 | C4/C5 smoothness numbers were captured on the wrong layer (activity window, not WebRender content) | gfxinfo reports only the main process (UI thread); the real content layer is a SurfaceView under HomeActivity#0 | verify via `dumpsys SurfaceFlinger --list` — confirmed `SurfaceView - ...HomeActivity#0`; use SurfaceFlinger latency for content frame timing |

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
| E8 | generated patch 005 lost its `diff --git`/`index` header on first write | `sed '1,2d'` stripped the ---/+++ pair before the header replacement could run | insert header before first hunk; verify with `git apply --check` on a fresh post-004 checkout, then full 001→005 sequence on a clean worktree |
| E9 | `git add -A` staged a 148 MB APK even though `.gitignore` listed `op7apk/` | gitignore does NOT support inline comments — `op7apk/  # comment` makes the whole line a pattern that never matches; only `#` on its own line is a comment | move comments to their own lines; verify with `git check-ignore -v <path>` before committing large files |
| E10 | handoff theory ("settings rows sit on container_low/lowest") was wrong for the main list | Preference styleable has no android:background; preference_material.xml root uses only selectableItemBackground ripple; PreferenceFragmentCompat draws rows over colorBackground with a #1f000000 divider | verified against androidx.preference 1.2.1 AAR (preference-1.2.1.aar) + upstream fenix styles.xml before patching; fixed the actual structure carriers (row surface + dividers) instead of only tokens |
| E11 | regenerating patch 005 needed real upstream blob hashes | r5 patch's index lines were hand-assembled (before-hash d74cdcb ≠ upstream blob cee5b72) | rebuilt 005 from pristine upstream files in a scratch git repo so index lines are true content hashes; verified git apply --check on fresh baseline and after 004; result files byte-identical to intended state |

### F. UI / perceived performance

| # | Problem | Root cause | Solution |
|---|---|---|---|
| F1 | visible color jump between splash and home screen on launch | hard-coded splash brand color (#FCF3EE / #210340) differs from home surface (#F7F6FB / #1D1B1F) | splash background references @color/fx_mobile_surface (patch 004) — seamless iOS-style launch, cosmetic only |
| F2 | dark theme uses dark-grey surfaces (#1d1b1f/#312f33), not true black, so AMOLED pixels stay lit | values-night/colors.xml maps Material3 surface tokens to novaGray65-85 / photonDarkGrey30/80 | patch 005 remaps surfaces to #000000 scale with subtle elevation steps (#070707-#242424); contrast 18.6:1 preserved; light theme untouched |
| F3 | after r5 AMOLED patch, the browser Settings page rendered as a pure-black void ("Only browser settings page black") | androidx.preference rows are transparent ripples over the activity colorBackground (fx_mobile_background = #000000) and its list divider is #1f000000 (invisible on black); no container token reaches the rows, so raising container_low/lowest alone would NOT fix the main settings list | r6 gives preference rows a real card surface — new @layout/op7_preference_row (derived from androidx preference_material 1.2.1, inset 12dp card, rounded 12dp, fill ?attr/colorSurfaceContainer = #1A1A1A = home-card tone) wired via PreferenceTheme.preferenceStyle + SwitchCompatPreferenceMaterialStyle; androidx list dividers neutralized (transparent) so full-width lines don't cross card gaps; container scale lifted off pure black (lowest #0A0A0A < low #121212 < container #1A1A1A < high #1F1F1F < highest #242424) so Compose sub-screens using colorSurfaceContainer* stay visible; background/surface/dim stay true black |

### G. Playbook & knowledge

| # | Problem | Root cause | Solution |
|---|---|---|---|
| G1 | full journey tables (docs/09, projects/*/README.md) cost agents too many tokens | every entry rendered in one big markdown table; an agent must read all of it to find one answer | notes/ layer — INDEX.md keyword->ids map (grep-able, ~150 lines), one entries/<id>.md per problem, lookup.py ranked search; agents read only the matching entry |
| G2 | keyword auto-extraction produced a noisy index (478 lines of '1.5', '2-core', 'add') | naive tokenization of problem+cause+solution text | curated INDEX from problem text + explicit tags only; full text kept in index.json for ranked lookup.py matching; stopwords + prefix-collapse |
| G3 | conversation digests lived only in the build repo, not the playbook | playbook sync fetched only log.yml | sync also lists docs/field-notes/sessions and fetches each *.md (skip _template) into _logs/sessions/<slug>/; SESSIONS.md generated with summaries |
| G4 | optional tags would be stripped by session_to_notes re-render | canonical renderer wrote only id/problem/cause/solution | renderer + digest parser now carry tags: [...] through |
| G5 | playbook was stale after a push — it only synced weekly + manual, and nothing triggered it on build-repo pushes | playbook-sync.yml scheduled `0 3 * * 1` (Monday only); no repository_dispatch/PAT wiring from the build repo | playbook-sync now polls every 6h (`0 */6 * * *`) — self-contained, no cross-repo secrets, also resets GitHub's 60-day scheduled-workflow window; manual dispatch used immediately |
| G6 | the original user engineering specification (ROLE, 35 requirements, success criteria) and day-to-day operating rules were not preserved verbatim anywhere | playbook carried only distilled golden rules (AGENTS.md, skill); the master prompt lived only in the conversation | added docs/00-master-spec.md to the playbook (canonical contract: engineering spec + Part B user operating rules: no local builds, Shizuku not adb, free infra only, 30-min windows, daily-driver care, playbook auto-update) and wired it into the skill references |
| G7 | conversations were only summarized by hand-written digests; raw chat knowledge was not systematically captured | session digests depend on the agent writing them; nothing read the actual Codex session files | new local tool automation/op7/conversation_to_notes.py extracts ONLY useful typed knowledge (RULE/DECISION/REQUEST/GOTCHA/GOAL, trimmed ≤300 chars, newest-first, noise-filtered) from ~/.codex/sessions JSONL into docs/field-notes/conversations/; playbook sync fetches them and renders notes/<slug>/CONVERSATIONS.md; raw transcripts are never stored |
| G8 | conversation extraction initially included system-injected noise (recommended_plugins block) and dropped the newest messages under the entry cap | injected preamble arrives as a user-role message; chronological collection hit the 40-entry cap first | NOISE regex filter (recommended_plugins/permissions/environment tags) + newest-first sort so today's knowledge always survives trimming |

### Recurring failure signature

If output is "sometimes there, sometimes not": it is almost always a transport
race, not the command. Fix by staging on-device + verifying size/content, then
retry. This pattern solved the most frustrating debugging hours.

<!-- generated; do not hand-edit -->
