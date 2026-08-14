# DeepDenoiser OP7

> Auto-generated from `projects/deepdenoiser-op7/manifest.yml` and the
> project's field-notes log. Do not hand-edit the journey section.

## Project

| Field | Value |
|---|---|
| Description | OnePlus 7 edition of the DeepDenoiser audio/video denoiser (Expo/ONNX DeepFilterNet3) |
| Build repo | https://github.com/rajbhx/deepdenoiser-op7 |
| Upstream | https://github.com/sayampy/deepdenoiser |
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

### A. Build pipeline & dependencies

| # | Problem | Root cause | Solution |
|---|---|---|---|
| DD1 | upstream deepdenoiser ships no dependency lockfile | bun.lockb/bun.lock gitignored upstream (expo/rn convention) | pin deps in overrides/bun.lock copied into the CI mirror before bun install --frozen-lockfile |
| DD2 | eas build --local requires EAS project ownership/token, unavailable to a new build repo | upstream CI depends on EAS cloud credentials | replace eas with expo prebuild + plain gradle assemble in the OP7 pipeline; no EAS dependency |
| DD3 | ONNX runtime native libs require matching NDK/ABI or gradle fails | onnxruntime-react-native builds JNI via CMake; arm64-v8a only | mirror upstream proven combo (Java 17 + NDK r28b + app.json buildArchs arm64-v8a); badging gate checks lib/arm64-v8a |
| DD6 | deepdenoiser CI build fails compiling @siteed/audio-studio (Promise.reject override mismatch) | fresh bun.lock resolved siteed 3.2.1; its reject(String?,...) no longer matches expo-modules-core Promise.reject(String,...); upstream patch-package patches target 3.0.3 | pin @siteed/audio-studio to 3.0.3 in overrides/bun.lock; verify compile passes |

### B. Android 10 & runtime stability

| # | Problem | Root cause | Solution |
|---|---|---|---|
| DD4 | android 10 install can fail on testOnly or signature mismatch | injected testOnly flag / per-build debug keystore | aapt badging gate rejects testOnly; stable DEBUG_SIGNING_KEY secret for consistent signatures |
| DD5 | repeated denoise jobs grow memory on OP7 (one InferenceSession leaked per job) | process.tsx handleDenoise creates a DeepFilterNet and never calls release(); recording flow already releases via ref | OP7 patch 001 - declare denoiser outside try, release() in finally (session is null-safe) |

<!-- generated; do not hand-edit -->
