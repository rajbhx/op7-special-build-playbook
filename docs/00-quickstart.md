# 00 — Quickstart: order of operations

The phase order is enforced, not suggested. Skipping it caused every rework.

## Before anything: refresh this skill

Agents should run the skill's self-update at session start so the playbook
knowledge is current:

```
bash /root/.shared-skills/op7-special-build/scripts/update_skill.sh
```

(cheap `git ls-remote` check; sparse fetch + atomic swap only when the
playbook repo moved; offline keeps the current copy).

1. **Audit** the existing app repo (workflows, build system, release system).
2. **Build unmodified** — prove the stock build works before touching anything.
3. **Record the baseline** — upstream commit, versions (browser, GeckoView/engine, Gradle, JDK, SDK), exact build command, APK SHA-256, ABI.
4. **Measure on the real device** — cold/warm start, memory, gfx, battery. Contended (in-use) numbers are better than nothing but must be labeled.
5. **Only then optimize** — one change per revision, benchmarked before/after.
6. **Automate upstream sync** — detect → sync → patch → build → validate → release, with conflict = stop + issue.

## Readiness gate

| Phase | Ready when | Status in this project |
|---|---|---|
| Baseline build (r0/r2) | CI build green, APK installs | ✅ done (r2 installs via Shizuku) |
| Clean Phase-2 measurements | ~15 min idle device window | ⏳ pending (contended numbers captured) |
| Phase-5 DeviceCapabilities | baseline recorded | ✅ design done; Kotlin impl gated on clean baseline |
| First optimization | baseline + capability detection | ⏳ |

Rule of thumb: if the device is being used while you measure, record it as
"contended" in the data — do not present it as a clean baseline.
