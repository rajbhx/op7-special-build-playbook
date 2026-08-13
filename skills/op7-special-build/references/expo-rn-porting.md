# Porting an Expo / React-Native app to OP7 (canonical reference)

Learned while porting `sayampy/deepdenoiser` (Expo 55, RN 0.83.6, React Native
0.83, onnxruntime-react-native 1.24.3, Kotlin MediaCodec module). Free GitHub
Actions only. No local builds.

## Verified OP7 compatibility facts

- minSdk: RN 0.83 + Expo 55 → minSdk 24 → **Android 10 (API 29) is supported**.
- The Expo template targetSdk tracks `compileSdk` (here 36). A higher targetSdk
  still *runs* on Android 10; scoped-storage enforcement applies to the app's
  storage accesses, NOT to the build.
- arm64-v8a: pin via `expo-build-properties` → `buildArchs: ["arm64-v8a"]`
  (app.json). This is a build-config override, not a source patch.
- NDK: ONNX Runtime JSI is built via CMake; must install the exact NDK the
  `onnxruntime-react-native` build.gradle pins (here r28b = 28.1.13356709).
  Use `nttld/setup-ndk` with `ndk-version: r28b` (proven upstream combo).
- Java: AGP 8.x needs JDK 17; match the upstream workflow (Temurin 17).

## Do NOT use EAS as an outsider build repo

- `eas build --local` still requires `EXPO_TOKEN` + EAS project ownership
  (the upstream `eas.json` projectId belongs to the upstream owner). A new build
  repo cannot use it.
- **Remedy:** `bunx expo prebuild --platform android --no-install` then plain
  `./gradlew assembleRelease/Debug`. Same toolchain, no EAS dependency.

## Reproducibility

- Expo/RN projects often ship NO lockfile (here `bun.lockb`/`bun.lock` are
  gitignored). A build repo **must** pin deps: generate `bun.lock` once and
  carry it as an override (`overrides/bun.lock`), copied into the CI mirror
  before `bun install --frozen-lockfile`. Always re-generate on upstream sync.

## Validation gate (aapt badging) must verify

- package name == expected
- `minSdkVersion` ≤ device API
- `native-code: 'arm64-v8a'` AND `lib/arm64-v8a/` present (ONNX JSI libs)
- `testOnly` is ABSENT (the Android-10 "App not installed" killer)
- SHA-256 + apk-metadata.json

## Patch discipline

- Patch-package patches (`patches/` in the app repo, e.g.
  `onnxruntime-react-native+1.24.3.patch`) are applied by `bun install`
  postinstall; they run INSIDE the upstream postinstall and are preserved by
  cloning upstream. Do not re-implement them.
- OP7-specific changes are separate `patches/op7/NNN-*.patch` applied via
  `git apply --3way` over the pinned upstream commit in CI.
- A genuine stability finding (not perf): ONNX `InferenceSession` created per
  denoise job but never released → memory leak across repeated jobs. Classified
  as stability/maintenance; recorded as OP7 patch 001. Perf tuning (thread
  counts, EP selection) is deferred until an on-device baseline exists.

## Android-10 gotchas seen here (all handled by upstream)

- Scoped storage: use content:// URIs (MediaStore/pickers); raw /storage paths
  break on API 29+.
- WRITE_EXTERNAL_STORAGE is a no-op on API 29+ → harmless to keep, but don't rely
  on it; use `expo-media-library` granular permissions.
- Foreground service for background recording needs
  FOREGROUND_SERVICE[_MEDIA_PLAYBACK]; on API 34+ the type must be declared.
