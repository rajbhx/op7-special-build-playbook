# 07 — On-device benchmarking that you can trust

## Protocol (real device only)

- Same device build/OxygenOS state; fixed brightness; airplane mode for CPU/startup tests.
- Phone idle ≥ 2 min before runs; 3–5 repeats; report median + min/max.
- Same profile state: fresh profile for cold tests.
- Production build variant, no benchmark-cheat flags.

## Metrics cheat-sheet

| Metric | Command |
|---|---|
| Cold start | `am force-stop` (verify pid gone) → `am start -W -n <pkg>/<Activity>` → keep runs with `LaunchState: COLD` |
| Warm start | activity must be finished while process alive (HOME/backgr ou d; note: HOME fails in proot env, needs adb) |
| Memory | `dumpsys meminfo <pkg>` (Java Heap, Native Heap, Graphics, TOTAL PSS) |
| GPU/frames | `dumpsys gfxinfo <pkg>` — total frames, janky %, 50/90/95/99th percentiles |
| Battery | `dumpsys batterystats --reset`, fixed idle window, then `dumpsys batterystats` |
| Media | MediaCodecList hardware decoders (H.264/HEVC/VP9 already verified on OP7) |

## Measurement pitfalls (all hit in practice)

- `am start -W` returns `TotalTime: 0` when the activity is already top-most — that is NOT a warm-start number. Filter `LaunchState`.
- Force-stop verification must check pid output, not transport exit code (Shizuku mangles exit codes).
- Active user usage during capture = "contended" data. Label it; a clean idle re-capture is required before optimization decisions.
- gfxinfo makes sense only after the UI actually rendered frames; capture after a normal use session, not on a blank first frame.
- Record conditions alongside every capture (transport, profile state, user activity, charge state).

## Decision rule

Keep an optimization only if the primary metric improves AND memory/battery/stability/web-compat stay within ±5% tolerance. One benchmark improving while another regresses = reject.
