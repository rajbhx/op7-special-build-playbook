# 10 — Porting this to another app (step-by-step)

Goal: a device-specific build of app X for custom device Y, automatically kept
in sync with app X upstream, on free GitHub infrastructure only.

1. **Inventory the app repo**
   - List workflows, build system (Gradle version, variants), release automation, version scheme, ABI coverage, patch conventions.
   - Verify target-device assumptions on real hardware (model, SoC, ABI, GLES/Vulkan, codecs, RAM). Never trust the brief.

2. **Prove the unmodified build** (stock commit, stock config) and record the baseline.
   - `docs/baseline.md` fields: upstream commit, app version, engine/library versions, Gradle/JDK/SDK, build command, APK path, SHA-256.

3. **Set up the patch layer**
   - `patches/<project>/NNN-*.patch`, applied in order over the exact upstream commit; every patch documents problem/root cause/layer/benefit/benchmark/risk.

4. **Wire the CI**
   - `ci.yml` (cheap validation on push/PR), `op7-build.yml` (dispatchable full build with inputs: upstream_commit, abi, release, fast, release_tag), `upstream-check.yml` (daily, cheap), `maintenance.yml` (monthly prune).
   - Caching: Gradle v2 action; Android SDK; Rust/Cargo; Maven; keys include OS/arch/toolchain/config.
   - Signing: dev key in repo secrets; release key in protected environment with guards.

5. **Quality gates before release**
   - badging (package, min/target SDK, native-code ABI, not testOnly, libs present) → compile/test → sign → SHA-256 → metadata → GitHub Release.

6. **On-device benchmarking (only on real hardware)**
   - `automation/op7/baseline_capture.sh` pattern: cold/warm start, meminfo, gfxinfo, batterystats; label contended data; filter `LaunchState: COLD`.

7. **Optimize one at a time**
   - Baseline → change → benchmark → compare → keep or revert. One optimization per revision. Never damage memory/battery/stability/web-compat for one benchmark.

8. **Long-term automation**
   - Daily upstream check (never builds) + sync issue + build dispatch; conflict → stop + issue; monthly cleanup; full pipeline restart after validation passes.

## Checklist before first release of any port

- [ ] Stock build reproduces from the documented command
- [ ] Badging: right package + ABI + SDK, no testOnly
- [ ] Installs via `pm install -r` WITHOUT `-t`
- [ ] Debug-sign + SHA-256 + metadata artifacts exist
- [ ] Release env secrets guarded; PRs never see them
- [ ] Maintenance workflow armed; artifact/cache retention set
- [ ] Upstream conflict → stop/report path tested
