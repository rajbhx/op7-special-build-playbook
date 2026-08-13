# Master spec (load when you need the full engineering contract)

The complete user engineering specification + user operating rules live in the
playbook clone at `docs/00-master-spec.md` (this file is just the pointer).

Load it when: starting a new special-build project, resolving a rule conflict,
writing a patch header, deciding whether a change is in scope, or explaining to
a user why the pipeline behaves a certain way.

One-line summary for cheap recall:
- Build = Iceraven/Fenix + GeckoView, thin OP7 patch layer, arm64-v8a only.
- Baseline first, one measured optimization per revision, revert on regression.
- Never publish an unvalidated build; upstream conflicts stop the pipeline.
- GitHub Actions free infra only; never build the APK locally; device driven
  via Shizuku, not adb.
- Phases 0→10 in order; smallest change that solves the measured problem.
