# Workflow — native-ai-op7 (DRAFT)

> Exact commands must be verified against the repo's own CI (phase 1) before
> relying on them. All builds run on GitHub Actions — never locally.

## Build
- Fast iteration (no R8): `./gradlew :app:assembleDebug`
- Full build (validated only): `./gradlew :app:assembleRelease`
- CI: `.github/workflows/build.yml` (checkout with `submodules: recursive`,
  Vulkan toolchain `libvulkan-dev shaderc`, arm64-v8a splits only)
- Reproduce submodule: `git submodule update --init --depth 1 third_party/llama.cpp`
  (pinned b10428 — never bump silently)

## Test / lint
- `./gradlew :app:testDebugUnitTest :app:lintDebug`
- JNI/API gate: grep every `llama_*` symbol used in `app/src/main/cpp/`
  against the pinned `third_party/llama.cpp/include/llama.h` (no obsolete API)

## Install to device
- `pm install -r <apk>` via Shizuku (never `-t`; reject testOnly in badging)
- Validate: `aapt dump badging <apk>` — expect arm64-v8a, no `android:testOnly`

## Benchmark (see playbook docs/07-on-device-benchmarking.md)
- cold start: `am start -W com.engine.nativeai/.MainActivity` (before/after)
- memory: `dumpsys meminfo com.engine.nativeai` (AI budget <= 1.5 GB; label data "contended" when the device was in use)
- inference: engine diagnostics — tokens/sec, first-token latency, prompt/generated tokens, KV estimate, GPU layers (spec §23)
- model load + backend: `nativeGetMemoryStats()` / `nativeGetBackendInfo()` via JNI

## Field notes
Every problem/solution goes in the build repo's `docs/field-notes/`
(session digest -> `log.yml`), same as iceraven-op7 — the playbook sync
picks it up automatically.
