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

- `status: active` — phases 0/1/3 done (CI baseline + badging gate + JVM unit
  tests); phase 2 (device baseline) awaits the OP7 on adb.
- Audit-first rule (spec FIRST TASK): compatibility verdict per subsystem before
  Phase 1 code — llama.cpp API (done vs pinned b10428), NDK toolchain, Snapdragon
  855 ARM64 features, Adreno 640 Vulkan, KV-cache quantization, GGUF mmap, CMake,
  JNI, Android 10 foreground-service restrictions, on-device LoRA feasibility.
- Spec Phase 1 done: NativeEngine RAII split, MemoryMonitor, streaming
  (Flow<String>, sampler chain, stop sequences, cancellation).
- Spec Phase 2 done: MemoryDatabase.kt (SQLite + FTS5) — CI green (f2486d3).
- Spec Phase 3 done: ReAct ThinkingAgent + tools + ActionParser + ContextManager
  (a49524c), then SafeExpr fix (40afb2c).
- Provider abstraction layer (d9ef943 + 546c795): ModelProvider interface,
  LocalModelProvider + OpenAICompatibleProvider (SSE, zero new deps), ModelRegistry
  dynamic catalog, ModelRouter (HYBRID/FREE_FIRST/LOCAL_FIRST/OFFLINE_ONLY),
  health monitor + fallback chain, ContextAdapter, MemoryPrivacyFilter,
  ModelBenchmark, model_info tool; ThinkingAgent routes via the router.
- OxygenOS "NEVER SETTLE" UI (33c8f0b): design tokens, Model Hub cards, segmented
  mode selector, Agent Trace with Horizon Light pulse.
- Source research audit (9b1e8d8): docs/source-research/ in the build repo
  (ADR-001..010 + inference/agents/memory/tools/permissions/ui/license docs).
- Math/hardware system spec applied (1a10566): Op7SystemProfile (1536 MB
  budget breakdown, affinity 0xF0, λ=0.05 decay, 85% context watermark),
  MemoryBudget equations, BM25×exp(-λ·Δt) retrieval, formal agent state
  machine (IDLE→UNDERSTAND→PLAN→EXECUTE→OBSERVE→VERIFY→FINALIZE→STORE/
  REPLAN→PLAN) with Stage events in the trace, docs/SYSTEM-PARAMETERS.json.
- Phase 5 done: ToolPermission (READ_ONLY/SAFE/REQUIRES_APPROVAL/PRIVILEGED)
  enforced in ToolExecutor + Verifier (tool/memory-claim checks).
- Phase 6/8 spec: skills (Skill/Registry/Storage/Manager), sessions
  (start/end/recent), SelfLearningPipeline (verified JSONL export + LoRA
  eligibility gate that never silently trains).
- Blueprint Phase 2 done: hardware_detector (topology, highCores 4-7,
  /proc/self/statm RSS), thread pinning via affinity inheritance, logcat
  init/pin lines, MemoryWatchdog (1.5 GB ceiling).
- Blueprint Phase 6 done: Jetpack Compose OxygenOS dashboard (Model Hub,
  segmented modes, Live Agent Trace, Horizon Light) — CI green (2530e27).
- Math/hardware spec CI green (1a10566 at 31807594038; head efd0a3e green at
  31808703429, docs-only after 31808113436).
- Spec Phase 5 done: EngineForegroundService (d4570d7, green 31808113436) —
  specialUse FGS holds engine+memory, 10s RSS watchdog vs 1.5 GB ceiling,
  learning eligibility ~5 min, Start/Stop toggle + POST_NOTIFICATIONS request.
- Self-learning (spec Phase 4) done: SelfLearningPipeline verified JSONL export
  + LoRA eligibility gate (never silently trains; dataset preserved for
  external training).
- Notes logged through A17 (FGS manifest requirements at targetSdk 34).
- Next: on-device benchmarks (playbook Phase 2/7/8 — threads 2-6, GPU layers,
  tokens/sec, first-token latency, RSS vs 1.5 GB, sustained perf primary) once
  the OP7 is on adb; upstream llama.cpp auto-sync (playbook Phase 4);
  experimental LoRA (spec Phase 6) stays eligibility-gated.

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
