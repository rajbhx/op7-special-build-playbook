# Onboarding — native-ai-op7 (DRAFT)

> Brief for whichever agent picks up this project next. Read the playbook
> `AGENTS.md` + `docs/00-quickstart.md` and the repo's
> `docs/GOLD-STANDARD-SPEC.md` before starting.

## What this project is

- Build repo: `https://github.com/rajbhx/native-ai-op7` (public)
- Stack: Kotlin (Foreground Service) + C++17 (llama.cpp JNI, Vulkan) +
  SQLite3 (FTS5) + CMake; arm64-v8a only; target OnePlus 7 (Snapdragon 855).
- Engine: **native** — bespoke engine, not an app fork. llama.cpp submodule is
  pinned (b10428); changes to it live in `patches/op7/` as thin patches.
- Status: `planning` — skeleton pushed; phase 0 (audit) in progress.

## First steps (audit-first — spec FIRST TASK)

1. **Audit (phase 0)** — produce COMPATIBLE / PARTIALLY COMPATIBLE /
   INCOMPATIBLE per subsystem: llama.cpp API (already done vs b10428), NDK
   toolchain, Snapdragon 855 ARM64 features, Adreno 640 Vulkan, KV-cache
   quantization, GGUF mmap, CMake, JNI, Android 10 foreground-service
   restrictions, on-device LoRA feasibility within the 1.5 GB budget.
2. **Prove the unmodified build (phase 1)** — dispatch CI
   (`.github/workflows/build.yml`, fast=true) until the APK builds; record
   toolchain versions + APK SHA-256.
3. **Measure on the real device (phase 2)** — cold start, memory, CPU;
   label data "contended" when the device was in use.
4. Only then optimize — one measured change per revision, benchmarked
   before/after, revert on regression.

## Rules that apply

- Baseline before optimization; never optimize on assumptions.
- Never exceed the 1.5 GB AI memory ceiling — redesign, don't violate.
- Never use obsolete llama.cpp API; adapt to the pinned checkout.
- Never publish an unvalidated build; GitHub Actions only, free infra.
- Record every problem/solution in the build repo's `docs/field-notes/`.

## Draft provenance
Created by the project-intake skill, reviewed + filled for native-ai-op7.
