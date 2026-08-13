# 00 — Master Engineering Specification (canonical)

The original build request this whole project is executing, preserved so any
agent (or human) can re-derive **why** every rule exists. This is the source of
truth for constraints; `docs/00-quickstart.md` is the operational order of
steps; `AGENTS.md` and the skill carry the distilled rules.

## ROLE (from the original prompt)

Act as a senior Android, GeckoView, Mozilla build-system, GitHub Actions,
CI/CD, performance-engineering, and open-source maintenance engineer working on
`fork-maintainers/iceraven-browser`, creating a OnePlus 7 optimized Iceraven
distribution while preserving the original Iceraven/Mozilla architecture and
making the project automatically maintainable as upstream changes.

- Do NOT create a new browser. Do NOT rewrite Firefox.
- Do NOT replace GeckoView with Android System WebView.
- Do NOT fork large portions of the code unnecessarily.

## Source of truth

Iceraven is a fork of Mozilla Fenix using GeckoView and Mozilla Android
Components. Treat the existing repo structure/build system as authoritative.
Inspect before changing: `.github/workflows`, `app`, `android-components`,
`automation`, `benchmark`, `config`, `gradle`, `plugins`, `mozconfig.json`,
`build.gradle`, `settings.gradle`, existing release automation. Do not
duplicate functionality that already exists; extend existing mechanisms.

## Primary objective

Iceraven + OnePlus 7 engineering, not a new Android browser. Retain: Gecko,
GeckoView, Android Components, browser architecture, web compatibility,
browser functionality, security architecture, extension support, privacy.
OP7 changes must be minimal, measurable, documented, easy to maintain.

## Target hardware (assumptions — verify, don't trust)

OnePlus 7: Snapdragon 855 / SM8150, ARM64/AArch64, Adreno 640, Android 10 /
OxygenOS 10, expected APK ABI `arm64-v8a` (Iceraven documents ARM64 for newer
64-bit devices). Verify build/device characteristics before implementing
hardware-specific behavior.

## Golden rule — baseline first

1. Build current Iceraven source unmodified. 2. Record upstream commit,
Iceraven/GeckoView/Android-Components versions, Gradle, JDK, SDK config, native
arch, build config → `docs/baseline.md`. 3. Only then optimize. Never optimize
based on assumptions.

## Device-aware engineering

Prefer a `DeviceCapabilities` architecture over scattered `Build.MODEL`
checks. Capabilities: ABI, API level, CPU arch/features, memory class, RAM,
GPU/graphics, Vulkan, OpenGL ES, MediaCodec, display, storage. A device-specific
workaround is allowed only if the problem is reproducible, root cause
understood, workaround necessary, benefit measurable, and it does not
unnecessarily damage other devices. If a generic Android capability check
solves it, use that instead.

## Architecture map (`docs/architecture.md`)

Iceraven → Android UI → Android Components → GeckoView → Gecko (Rust, C++,
graphics, networking, media, Java/JNI). Fix each problem in the correct layer:
never fix a Gecko problem in the Android UI; never fix an Android lifecycle
problem inside Gecko.

## Performance engineering

Profile baseline first: cold/warm startup, first UI, first page load, heavy
page load, scrolling, tab switching, JS-heavy, image-heavy, video playback,
downloads, memory, CPU, GPU, background behavior, battery. Record in
`docs/performance/baseline.md`.

- CPU/ARM64: investigate native libs, Rust, C/C++, JNI, compiler config, CPU
  feature detection. No blind `-march=native`; no hard-coded optional
  instructions without detection. Preserve portability. Benchmark → implement →
  test → benchmark → document.
- GPU/Adreno 640: profile WebRender, compositor, OpenGL ES, Vulkan, frame
  rendering, scrolling, animations, GPU utilization, memory. Only retain
  changes with measurable improvement.
- Memory: optimize long sessions (Gecko memory, content processes, Java heap,
  native allocations, image/browser caches, tabs, suspended tabs, extensions,
  SQLite, background). Test 5/10 tabs, heavy pages, media pages. Do not disable
  caching/features to fake lower numbers.
- Startup: stage analysis (Android process → Iceraven UI → GeckoView → Gecko →
  profile → first UI → first page); optimize measured bottlenecks.
- Media: inspect actual device codec capabilities (H.264/HEVC/VP9 etc.), verify
  GeckoView uses hardware acceleration, provide safe software fallback.
- Storage/UFS: profile profile init, SQLite, cache, startup I/O, downloads;
  reduce only profiled I/O. Never modify filesystem/vendor config.
- Networking: preserve Firefox networking (DNS, HTTP/2/3, TLS, connection
  reuse, cache). No hard-coded DNS provider; never bypass privacy/security.
- Battery/thermals: optimize sustained performance — wakeups, timers, polling,
  background work, network, rendering, memory churn. No short synthetic
  benchmark chasing; prefer stable long sessions.

## Patch architecture

Keep custom changes identifiable and compatible with the repo. Document every
patch: problem, root cause, affected layer, implementation, expected benefit,
benchmark, regression risk, upstream relationship.

## Upstream automation (critical)

Detect upstream changes → synchronize → apply OP7 changes → build → test →
validate → release. NEVER force-reset to upstream, NEVER destroy OP7 changes,
NEVER silently resolve complex conflicts. On conflict: STOP publishing, report
upstream commit, failing patch, conflicting files, conflict reason, last
known-good release, suggested maintenance area; open an issue if appropriate.
Never replace a working release with an unvalidated build.

## GitHub Actions

Primary CI/CD, public free runners. Prefer existing Iceraven workflows; logical
separation: `ci.yml`, `upstream-sync.yml`, `op7-build.yml`, `release.yml`,
`security.yml`, `maintenance.yml` — no duplicates of existing functions.
Triggers: push, pull_request, workflow_dispatch, schedule, repository_dispatch.
Scheduled workflows can be disabled after 60 days without activity → secondary
update mechanism required; the scheduled check must be lightweight (check
upstream, only build when changed).

## Build efficiency & free infrastructure

Cache Gradle/SDK/Rust/Maven/compatible build caches safely (keys: OS, arch,
toolchain, dependency, config); never cache stale binaries. No paid CI,
artifacts, hosting, monitoring, or proprietary systems. Be aware of GitHub
artifact/cache/storage limits.

## Release artifacts, signing, reproducibility, versioning

Publish APK + SHA-256 + metadata (base upstream commit, Iceraven version,
OP7 patch revision, workflow/run id, target ABI). Signing: dev builds use the
project's safe dev mechanism; public releases use a dedicated release key via
secrets/environment protection; never commit keys; never expose secrets to
untrusted-fork PR builds. Every release traceable (repo commit, upstream
commit, OP7 revision, workflow revision, build config) →
`docs/reproducible-build.md`. Extend Iceraven versioning, don't replace it.

## Quality gates (all mandatory)

Source sync → patches apply → dependencies resolve → compilation → tests →
APK generated → structurally valid → ABI correct → version metadata correct →
signing → checksum. If ANY gate fails: DO NOT RELEASE.

## Security (never trade for benchmarks)

Preserve Gecko sandboxing, site isolation, certificate validation, HTTPS,
process isolation, Android permission model, Firefox security mechanisms. Do
not disable security features because they consume resources.

## Observability

Every workflow produces summaries: source/upstream commit, changed files,
patch status, build duration, cache hit/miss, test status, artifact/release
status. Use GitHub Actions job summaries.

## Maintenance bot

Automated process: check upstream → synchronize → identify conflicts → build →
test → report → publish only after success. NEVER silently modify unrelated
project files.

## Benchmark regression

For every optimization: baseline → change → benchmark → compare → revert on
regression. Record in `docs/performance/`. Reject optimizations that improve
one metric while damaging memory, battery, stability, or compatibility.

## Development phases (enforced order — no skipping)

0 audit → 1 unmodified build → 2 baseline measurements → 3 GitHub Actions
reliability → 4 automatic upstream sync → 5 OP7 capability detection → 6
performance profiling → 7 first measured optimization → 8 benchmark/regression
system → 9 automated release pipeline → 10 long-term upstream maintenance.

## Do not overengineer

No unnecessary abstractions, services, scripts, workflows, duplicate build
systems, giant device-specific forks, or speculative optimizations. Smallest
change that solves the measured problem.

## Success criteria

Iceraven upstream → automatic detection → safe synchronization → OP7 patch
layer → GitHub Actions → build/test → quality gates → report on FAIL /
release on PASS → repeat on next upstream. Result: an automatically
maintained, reproducible, OnePlus 7 optimized Iceraven build on GitHub's free
public infrastructure, with upstream sync, automated validation, performance
regression tracking, and safe release automation. Do not sacrifice
maintainability, security, or upstream compatibility.

---

## Part B — User operating rules (from the actual sessions)

Hard constraints the owner enforces on this project day-to-day; treat as
binding for any agent working here:

- **Never build the APK locally.** All builds happen on GitHub Actions. Local
  work = repo edits, docs, patches, automation only.
- **Do not use adb here.** The device is driven via Shizuku (`shizuku sh -c
  "..."`) and a screenshot loopback server (screencap → curl to a local port).
- **Never commit unless the commit will be pushed.** No local-only commits, no
  branches unless asked.
- **Free infrastructure only** — GitHub Actions, Releases, caches; no paid
  services of any kind.
- **One measured optimization per revision** (`op7r<N>`); benchmark before/
  after on the real device; label measurements "contended" if the device was in
  use; revert on regression.
- **Patch iteration:** dispatch CI with `-f fast=true` (~13 min). Full release
  builds (~40 min) only when ready.
- **Never publish an unvalidated build.** Upstream conflicts stop the pipeline.
- **The phone is the owner's daily driver — be careful.** Do not uninstall or
  disable apps without a restore plan; avoid destructive operations.
- **The playbook must auto-update from our conversations.** Every solved
  problem → field-notes digest → `session_to_notes.py` → commit+push → playbook
  sync regenerates the searchable layer. Agents read only what they need
  (low-token pattern).
- **Keep it understandable for other AI agents.** Favor explicit, searchable,
  token-cheap knowledge files over long prose.
- **Only arm64-v8a.** Never package all three ABIs (triples time + artifact
  size).
- **30-minute bandwidth windows** — when the user says bandwidth is limited,
  avoid large downloads; do the work that needs the network first, prioritize.
- **Verify before building** — inspect the code and logs properly first; find
  root causes, don't guess.
