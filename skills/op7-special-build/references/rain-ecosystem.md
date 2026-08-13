# The Rain ecosystem (ra1ncord) — OP7 Android port

Learned while mapping `ra1ncord` org repos for the OnePlus 7 build. Canonical
upstream home is **Codeberg** (`raincord`); GitHub (`ra1ncord`) is a mirror.

## Repository map

| Repo | Lang | Role for OP7 Android build |
|---|---|---|
| `ra1ncord/rain` | TypeScript | Discord client core → `dist/rain.js` + `rain.hbc`; built by `bun run build --release-branch=main --build-bytecode` |
| `ra1ncord/rainManager` | Kotlin/Compose | **deliverable APK** — downloads Discord APK, patches it (smali + LSPatch), injects rain, installs via Shizuku/pm |
| `ra1ncord/rainXposed` | Kotlin | Xposed module injected at patch time by the manager; fetch live Codeberg release (reference pin only) |
| `ra1ncord/RainTweak` | C++/Theos | iOS jailbreak tweak — **excluded** from Android |

## rainManager facts

- minSdk 28 → Android 10 OK; targetSdk 36; compileSdk 36.
- `Manifest` sets `requestLegacyExternalStorage="true"` (honored on Android 10),
  `MANAGE_EXTERNAL_STORAGE` + `QUERY_ALL_PACKAGES` (API 30+, no-ops on 29),
  `REQUEST_INSTALL_PACKAGES` + `UPDATE_PACKAGES_WITHOUT_USER_ACTION`.
- Toolchain: JDK 21 (zulu), Gradle 8.14.3 wrapper, AGP 8.11.0, Kotlin 2.2.0.
- Uses the aliucord maven snapshot repo + committed `app/libs/lspatch.aar`.
- Native libs shipped as **assets** (`assets/lspatch/so/<abi>/liblspatch.so`),
  NOT as jniLibs → the manager APK has NO `lib/` entries; the patched Discord
  output inherits Discord's ABIs (arm64-v8a on OP7).
- Manager selects `Build.SUPPORTED_ABIS.first()` when injecting → correct ABI
  for OP7 (arm64).

## Android-10 install path

- PackageInstaller API (not `pm install` directly by the app): `PMInstaller`
  creates a session, streams the APK, and the system shows the confirm dialog.
  Requires Shizuku only for the *silent* install path; the user-facing flow uses
  the system dialog → works on Android 10 without Shizuku.

## Bundle build gotcha

- `hermes-compiler` is a devDependency with platform binaries; declare it in
  `trustedDependencies` and run `bun install` (not `bun install --frozen-lockfile`
  if the lockfile is missing — rain already ships `bun.lock`).
- Build command must be exactly `bun run build --release-branch=main --build-bytecode`
  to match the upstream Forgejo workflow.

## OP7-specific optimization idea (NOT yet applied)

- The 4 lspatch `.so` variants total 1.8 MB; OP7 only ever needs arm64-v8a.
  Shipping only `arm64-v8a` (or removing the others at build time) is a valid
  Level-2 size/patch-time optimization — but it must be MEASURED against an
  on-device baseline (patch-write time, APK size) and applied as a separate
  revision, never folded into a "fork".
