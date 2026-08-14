# Roadmap — native-ai-op7 (DRAFT)

> Playbook phases 0..10 (docs/00-quickstart.md) + the gold-standard spec's
> own phase plan (docs/GOLD-STANDARD-SPEC.md in the build repo). Baseline
> first, one measured optimization per revision, GitHub Actions only.

| Phase | Goal |
|---|---|
| 0 | Audit — build system (Gradle+CMake+NDK), pinned versions (Gradle 8.9, AGP 8.5.2, Kotlin 1.9.24, NDK 27, llama.cpp b10428), upstream relationship |
| 1 | Unmodified build — CI builds the stock checkout; record toolchain + APK SHA-256 |
| 2 | Baseline measurements — cold start, memory (AI budget <= 1.5 GB), CPU, thermal on the OP7 |
| 3 | CI reliability — build/test/lint + validation gates (badging, testOnly, arm64-v8a only) |
| 4 | Upstream auto-sync — track llama.cpp; thin patch layer in patches/op7/; conflicts stop the pipeline |
| 5 | Capability detection — Kryo 485 cores, Adreno 640 Vulkan, RAM, KV-cache quantization support |
| 6 | Profiling — llama.cpp decode/sampling, SQLite latency, agent loop, native allocations |
| 7 | First measured optimization — one change benchmarked before/after (threads, GPU layers, KV type) |
| 8 | Benchmark/regression system — tokens/sec, first-token latency, memory at 512/1024/2048 ctx |
| 9 | Automated release — signed APK + GGUF/LoRA artifacts only after all gates pass |
| 10 | Long-term maintenance — monthly cleanup + llama.cpp follow |

## Current state

- `status: planning` — DRAFT skeleton pushed; phase 0 (audit) is in-progress.
- Audit-first rule (spec FIRST TASK): compatibility verdict per subsystem before
  Phase 1 code — llama.cpp API (done vs pinned b10428), NDK toolchain, Snapdragon
  855 ARM64 features, Adreno 640 Vulkan, KV-cache quantization, GGUF mmap, CMake,
  JNI, Android 10 foreground-service restrictions, on-device LoRA feasibility.

## Project phases (gold-standard spec)

The spec defines its own implementation phases; they map onto the playbook
phases above (both stay in sync in manifest.yml):

| Spec phase | Scope | Playbook phase(s) |
|---|---|---|
| 0 | Repository architecture + dependency lock | 0, 3 |
| 1 | Native llama.cpp inference (JNI, streaming, MemoryMonitor) | 1, 5, 6 |
| 2 | SQLite + FTS5 fast memory | 5 |
| 3 | Agent orchestration + tools (ReAct, structured actions) | 6 |
| 4 | Verified self-learning dataset generation | 7 |
| 5 | Resource-aware background service | 2, 5 |
| 6 | Experimental on-device LoRA adapter training | 7 |
| 7 | Benchmarking + optimization | 2, 7, 8 |
| 8 | Production hardening | 9, 10 |

## External services (free infra only)

- GitHub Actions — all builds; GitHub Releases — APK artifacts.
- Hugging Face Hub — GGUF base models and LoRA adapter artifacts (never commit
  binaries to git). Everything else stays on-device.
