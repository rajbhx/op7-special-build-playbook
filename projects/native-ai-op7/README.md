# Native AI Engine OP7

> Auto-generated from `projects/native-ai-op7/manifest.yml` and the
> project's field-notes log. Do not hand-edit the journey section.

## Project

| Field | Value |
|---|---|
| Description | Self-learning agentic AI engine (llama.cpp + Vulkan + SQLite FTS5) for OnePlus 7, arm64-v8a only |
| Build repo | https://github.com/rajbhx/native-ai-op7 |
| Upstream | https://github.com/ggml-org/llama.cpp |
| Engine | native |
| Target device | OnePlus 7 (GM1901) |
| ABI | arm64-v8a |
| Status | planning |
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
| 5 | pending |
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

<!-- generated; do not hand-edit -->
