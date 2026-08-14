# Native AI Engine OP7

> Auto-generated from `projects/native-ai-op7/manifest.yml` and the
> project's field-notes log. Do not hand-edit the journey section.

## Project

| Field | Value |
|---|---|
| Description | Self-learning agentic AI engine (llama.cpp + SQLite FTS5, provider-neutral model routing, OxygenOS UI) for OnePlus 7, arm64-v8a only |
| Build repo | https://github.com/rajbhx/native-ai-op7 |
| Upstream | https://github.com/ggml-org/llama.cpp |
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
| 2 | pending |
| 3 | done |
| 4 | pending |
| 5 | done |
| 6 | pending |
| 7 | pending |
| 8 | pending |
| 9 | pending |

## Field notes (auto-synced)

### A. CI & build pipeline

| # | Problem | Root cause | Solution |
|---|---|---|---|
| A1 | llama.cpp submodule tag checkout fails in a shallow clone ('origin/b10428 is not a commit') | --depth 1 --branch <tag> fetches only the default branch, so release tags are absent | submodule add shallow, then fetch --depth 1 origin tag b10428 + checkout + git add the gitlink |
| A2 | 'E: Unable to locate package shaderc' on the Ubuntu 24.04 runner | shaderc was restructured in noble; llama.cpp's own CI uses glslc + spirv-headers | apt-get install -y glslc libvulkan-dev spirv-headers |
| A3 | 'GGML_CPU_ALL_VARIANTS requires GGML_BACKEND_DL' at CMake configure | llama.cpp gates ALL_VARIANTS behind dynamic backend loading (ggml/src/CMakeLists.txt:373) | set GGML_BACKEND_DL=ON together with GGML_CPU_ALL_VARIANTS=ON (mirrors llama.cpp build-android.yml) |
| A4 | 'Inconsistent JVM-target compatibility (1.8 vs 17)' fails compileDebugKotlin | AGP defaults Java target 1.8 while Kotlin jvmTarget defaulted to 17 | compileOptions VERSION_17 + kotlinOptions { jvmTarget = "17" } inside android {} |
| A5 | 'Unresolved reference ... BaseAppModuleExtension.kotlinOptions' in build.gradle.kts | kotlinOptions used at top level instead of scoped inside the android {} extension | move the block inside android {} |
| A6 | 'no matching function for call to llama_memory_clear' at b10428 | KV-cache API refactor — memory ops take a llama_memory_t handle, not the context | llama_memory_clear(llama_get_memory(g_ctx), false) with null guard |
| A7 | lifecycleScope unresolved in MainActivity (receiver mismatch) | lifecycleScope is a LifecycleOwner extension; plain Activity is not a LifecycleOwner | own CoroutineScope(SupervisorJob() + Dispatchers.Main), cancel in onDestroy, drop lifecycle-runtime-ktx |
| A8 | llama_load_model_from_file / llama_free_model deprecated at b10428 | llama.cpp renamed the model API (llama_model_load_from_file / llama_model_free) | use the current names, verified against the pinned header |
| A9 | sampler chain params at b10428 carry only no_perf — penalties missing | llama_sampler_chain_params has just no_perf; penalties are a separate sampler object | add llama_sampler_init_penalties(n_vocab, last_n, repeat, 0, 0) to the chain before top_k/top_p/temp/dist |
| A10 | SafeExpr compile error: 'inferred type is () -> Int but SafeExpr.Ref was expected' | parseExpr called with a trailing lambda { pos } instead of the Ref holder | val pos = Ref(0); parseExpr(tokens, pos); check pos.value != tokens.size |
| A11 | Redeclaration: ToolResult + 'Cannot find a parameter with this name: id/inputHash' | agent tool result duplicated the Phase 2 DB record name ToolResult (MemoryModels.kt) | rename tool-execution result to ToolOutput; the DB record keeps ToolResult |
| A12 | 'Returns are not allowed for functions with expression body' in parseSseEvent | unlabeled return null inside fun ... = try { } | make the if/else the try value; no bare return |
| A13 | 'Smart cast to ModelDescriptor is impossible — captured by a changing closure' | nullable var reassigned inside a catch while read inside flow lambdas | non-null via ?: run { emit(Error); return@flow }; var stays non-null |
| A14 | ld.lld: undefined symbol ggml_threadpool_new / ggml_threadpool_free | threadpool API lives in the CPU backend (ggml-cpu.c), dlopen'd under GGML_BACKEND_DL=ON — not linkable from native-lib | pin the calling decode thread before first graph compute; pthreads inherit creator affinity; no direct ggml-cpu link; -llog for logcat |
| A15 | setContent in MainActivity: 'receiver type mismatch' | androidx.activity.compose.setContent is a ComponentActivity extension; activity extended plain android.app.Activity | extend androidx.activity.ComponentActivity |
| A16 | memory retrieval ranked by hand-rolled linear recency, not the spec's BM25 × exponential decay | Phase 2 scoring predated the math spec (score = utility*0.5 + recency*0.3 + success*0.2) | ftsCandidates selects bm25(experiences_fts) AS bm25_rank; score = -rank * exp(-0.05*ageDays) + small tiebreaks; decay SQL lambda 0.02 -> 0.05 |
| A17 | FGS specialUse requires both the permission and the subtype property at targetSdk 34 | Android 14 introduced FOREGROUND_SERVICE_SPECIAL_USE with a required PROPERTY_SPECIAL_USE_FGS_SUBTYPE | declare FOREGROUND_SERVICE + FOREGROUND_SERVICE_SPECIAL_USE + POST_NOTIFICATIONS; service foregroundServiceType=specialUse + property; request POST_NOTIFICATIONS at runtime (API 33+) |
| A18 | setup-java v4 deprecation annotation; web_search ok flag coupled to a magic string | actions/setup-java@v4 is deprecated; WebSearchTool checked result.startsWith('web search unavailable') | migrate to actions/setup-java@v5; SearchProvider returns SearchResult(text, ok), LocalFallbackProvider ok=false; playbook phase 5 marked done |

<!-- generated; do not hand-edit -->
