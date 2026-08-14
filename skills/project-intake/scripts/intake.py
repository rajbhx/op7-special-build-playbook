#!/usr/bin/env python3
"""Project intake: classify a candidate source repo and draft playbook scaffolding.

Writes DRAFT files only (manifest.yml, roadmap.md, workflow.md, PROMPT.md) to
projects/<slug>/ (new) or intake-drafts/<slug>/ (existing folder -> diff shown).
Never guesses: uninferrable manifest fields stay literal TODO; repos that fit
no engine are flagged for enum extension and nothing is drafted.

Usage:
  python3 intake.py --repo <url|path> --slug <slug> [--out <playbook-root>] [--dry-run]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ENGINES = ("geckoview", "webview", "native", "other")
IGNORED_DIRS = {
    ".git", "node_modules", "build", "dist", ".gradle", "target", ".idea",
    "out", ".dart_tool", ".venv", "venv", "__pycache__", "Pods", ".cache",
    "third_party", "vendor",
}
MAX_DEPTH = 6
HEAD_BYTES = 8192

GECKOVIEW_MARKERS = (
    "org.mozilla.geckoview", "geckoview-omni", "org.mozilla:geckoview",
    "org.mozilla.components", "mozilla-central", "android-components",
)
WEBVIEW_MARKERS = ("android.webkit.WebView", "WebViewClient", "WebChromeClient")


class Detection:
    def __init__(self):
        self.signals = {}          # signal -> evidence lines
        self.engine = None         # final engine or None (unclassified)
        self.engine_note = ""
        self.abi = None
        self.abi_note = ""


def walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
        depth = dirpath[len(root):].count(os.sep)
        if depth > MAX_DEPTH:
            dirnames[:] = []
            continue
        for name in filenames:
            yield os.path.join(dirpath, name)


def read_head(path, size=HEAD_BYTES):
    try:
        with open(path, "r", errors="ignore") as fh:
            return fh.read(size)
    except OSError:
        return ""


def rel(root, path):
    return os.path.relpath(path, root)


def detect(root):
    d = Detection()
    gradle_texts = []
    java_kt_texts = []
    manifests = []
    pubspec = cargo = pkgjson = cmake = pyproj = None
    so_dirs = set()

    for path in walk_files(root):
        base = os.path.basename(path).lower()
        text = ""
        if base in ("build.gradle", "build.gradle.kts", "settings.gradle",
                    "settings.gradle.kts", "gradle.properties", "libs.versions.toml"):
            text = read_head(path, 64 * 1024)
            gradle_texts.append((rel(root, path), text))
        elif base == "androidmanifest.xml":
            manifests.append(path)
        elif base == "pubspec.yaml" or base == "pubspec.lock":
            pubspec = (rel(root, path), read_head(path, 64 * 1024))
        elif base == "cargo.toml":
            cargo = (rel(root, path), read_head(path, 64 * 1024))
        elif base == "package.json":
            pkgjson = (rel(root, path), read_head(path, 64 * 1024))
        elif base == "cmakelists.txt":
            cmake = rel(root, path)
        elif base in ("pyproject.toml", "requirements.txt", "setup.py"):
            pyproj = rel(root, path)
        elif base.endswith((".java", ".kt", ".kts")) and not base.endswith(".gradle.kts"):
            java_kt_texts.append((rel(root, path), read_head(path)))
        elif base.endswith(".so"):
            parent = os.path.basename(os.path.dirname(path))
            if parent in ("arm64-v8a", "armeabi-v7a", "armeabi", "x86", "x86_64", "arm64", "arm"):
                so_dirs.add(parent)
        elif base.endswith((".sln", ".csproj", ".xcodeproj", ".swiftpm")):
            d.signals.setdefault("dotnet/swift", []).append(rel(root, path))
        elif base == "gradlew":
            d.signals.setdefault("gradle-wrapper", []).append(rel(root, path))

    # --- Gradle / Android signals ---
    android_gradle = bool(gradle_texts) or bool(manifests) or "gradle-wrapper" in d.signals
    gecko_evidence = []
    for p, t in gradle_texts:
        for line in t.splitlines():
            if any(m in line for m in GECKOVIEW_MARKERS):
                gecko_evidence.append(f"{p}: {line.strip()}")
    webview_evidence = []
    for p, t in java_kt_texts:
        if any(m in t for m in WEBVIEW_MARKERS):
            webview_evidence.append(p)
    if manifests:
        d.signals.setdefault("android-manifest", []).extend(rel(root, m) for m in manifests)
    if android_gradle:
        d.signals.setdefault("gradle-android", []).append(
            f"{len(gradle_texts)} gradle file(s)" if gradle_texts else "gradlew only")

    if gecko_evidence:
        d.signals["geckoview"] = gecko_evidence
    if webview_evidence:
        d.signals["webview-usage"] = webview_evidence

    # --- Framework signals ---
    if pubspec and "flutter:" in pubspec[1]:
        d.signals["flutter"] = [f"{pubspec[0]}: flutter dependency"]
    if cargo:
        d.signals["rust"] = [f"{cargo[0]}: Cargo.toml present"]
        if "tauri" in cargo[1].lower():
            d.signals.setdefault("tauri", []).append(f"{cargo[0]}: tauri dependency")
    if pkgjson:
        d.signals["node"] = [f"{pkgjson[0]}: package.json present"]
        if '"electron"' in pkgjson[1]:
            d.signals.setdefault("electron", []).append(f"{pkgjson[0]}: electron dependency")
        if '"@capacitor' in pkgjson[1] or "capacitor" in pkgjson[1]:
            d.signals.setdefault("capacitor", []).append(f"{pkgjson[0]}: capacitor dependency")
    if cmake:
        d.signals["cmake"] = [cmake]
    if pyproj:
        d.signals["python"] = [pyproj]
    if so_dirs:
        d.signals["jni-abi"] = sorted(so_dirs)

    # --- Classification (first clean match wins) ---
    if gecko_evidence:
        d.engine, d.engine_note = "geckoview", "GeckoView/AC markers in gradle files"
    elif webview_evidence and not gecko_evidence:
        d.engine, d.engine_note = "webview", "android.webkit usage (no GeckoView)"
    elif "tauri" in d.signals or "electron" in d.signals or "capacitor" in d.signals:
        d.engine, d.engine_note = "webview", "system-WebView wrapper framework"
    elif "flutter" in d.signals:
        d.engine, d.engine_note = "native", "Flutter (compiled engine, not a webview)"
    elif "rust" in d.signals:
        d.engine, d.engine_note = "native", "Rust binary/library"
    elif "cmake" in d.signals or "dotnet/swift" in d.signals:
        d.engine, d.engine_note = "native", "compiled C/C++/.NET/Swift"
    elif "node" in d.signals:
        d.engine, d.engine_note = "other", "Node/JS project (no wrapper framework)"
    elif "python" in d.signals:
        d.engine, d.engine_note = "other", "Python project"
    else:
        d.engine, d.engine_note = None, "no recognizable build-system signal"

    # --- ABI (best effort) ---
    for p, t in gradle_texts:
        m = re.search(r"abiFilters\s+[\"']([^\"']+)[\"']", t)
        if not m:
            m = re.search(r"ndk\s*\{[^}]*abiFilters\s+([^\n}]+)", t, re.S)
        if m:
            d.abi = ",".join(sorted(re.findall(r"[a-z0-9_-]+", m.group(1)))).strip(",")
            d.abi_note = f"from {p}"
            break
    if not d.abi and d.signals.get("jni-abi"):
        d.abi = ",".join(sorted(d.signals["jni-abi"]))
        d.abi_note = "from jniLibs/.so dirs"
    return d


def report(d, repo_src, slug):
    lines = [f"# Intake report — {slug}", f"- repo: {repo_src}", f"- slug: {slug}"]
    if d.engine is None:
        lines.append(f"- engine: UNCLASSIFIED ({d.engine_note})")
    else:
        lines.append(f"- engine: {d.engine} — {d.engine_note}")
        lines.append(f"- abi: {d.abi or 'TODO'} {d.abi_note or ''}".rstrip())
    lines.append("- signals:")
    if not d.signals:
        lines.append("  (none)")
    for key in sorted(d.signals):
        for ev in d.signals[key][:8]:
            lines.append(f"  - {key}: {ev}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Draft templates
# --------------------------------------------------------------------------

def manifest_draft(slug, d):
    upstream = "TODO"  # never guessed; kept TODO unless provided
    return f"""# DRAFT — generated by project-intake. Review + adjust, then commit manually.
# Schema follows AGENTS.md; every field is present so CI validation passes.
# Anything that cannot be inferred stays a literal TODO (never guessed).
project:
  slug: {slug}              # must match this folder name
  name: "TODO"              # human-readable name — NOT inferred
  description: "TODO"       # one line — NOT inferred
  repo: TODO                # your build repo (public) — NOT inferred
  upstream_repo: {upstream}  # original app source
  engine: {d.engine}         # detected from the source tree
  target_device: "TODO"     # verified device, not assumed
  abi: {d.abi or "TODO"}     # detected when discoverable, else TODO
  status: planning          # draft: nothing shipped yet
  maintainer: TODO          # gh username — NOT inferred

  # Where this project's field-notes log will live (source for auto-sync).
  field_notes:
    repo: TODO
    path: docs/field-notes/log.yml

  # Phase status per docs/00-quickstart.md (0=audit ... 10=long-term maintenance)
  phases:
    "0": pending
    "1": pending
    "2": pending
    "3": pending
    "4": pending
    "5": pending
    "6": pending
    "7": pending
    "8": pending
    "9": pending
    "10": pending

  patches_ref: TODO         # where custom patches will live in the build repo
"""

PHASES = {
    "geckoview": [
        ("0", "Audit — inventory build system, GeckoView/AC versions, workflows, upstream relationship"),
        ("1", "Unmodified build — stock checkout builds; record baseline (upstream commit, versions, exact command, APK SHA-256)"),
        ("2", "Baseline measurements — cold/warm start, memory, gfx, battery on the target device (docs/07)"),
        ("3", "CI reliability — GitHub Actions build + validation gates (badging, ABI, testOnly)"),
        ("4", "Upstream auto-sync — detect -> sync -> patch -> build -> validate -> release; conflicts stop the pipeline"),
        ("5", "Capability detection — DeviceCapabilities layer (ABI, RAM, GLES/Vulkan, codecs)"),
        ("6", "Profiling — profile the unmodified baseline (startup, scroll, media, memory)"),
        ("7", "First measured optimization — one change, benchmarked before/after"),
        ("8", "Benchmark/regression system — keep a baseline; revert regressions"),
        ("9", "Automated release — signed release only after all gates pass"),
        ("10", "Long-term maintenance — monthly cleanup + upstream follow"),
    ],
    "webview": [
        ("0", "Audit — app structure, WebView usage, permissions, upstream relationship"),
        ("1", "Unmodified build — stock APK builds and installs on the target device"),
        ("2", "Baseline measurements — startup to first WebView paint, memory, scroll smoothness"),
        ("3", "CI reliability — build + lint + APK badging gates in GitHub Actions"),
        ("4", "Upstream auto-sync — track upstream app + WebView provider updates"),
        ("5", "Capability detection — device RAM/GPU/codecs (WebView settings depend on them)"),
        ("6", "Profiling — page load, scroll jank, JS bridge, cache behavior"),
        ("7", "First measured optimization — WebView settings/cache/pooling, benchmarked"),
        ("8", "Benchmark/regression system — keep a baseline; revert regressions"),
        ("9", "Automated release — signed release only after all gates pass"),
        ("10", "Long-term maintenance — monthly cleanup + upstream follow"),
    ],
    "native": [
        ("0", "Audit — build system (cargo/cmake/gradle), targets, artifacts, upstream"),
        ("1", "Unmodified build — reproduce the stock build; record toolchain + versions"),
        ("2", "Baseline measurements — startup, memory, CPU on the target device"),
        ("3", "CI reliability — build/test/lint in GitHub Actions"),
        ("4", "Upstream auto-sync — track upstream commits; thin patch layer"),
        ("5", "Capability detection — device capabilities relevant to the native stack"),
        ("6", "Profiling — profile the unmodified binary (CPU/memory)"),
        ("7", "First measured optimization — one change, benchmarked before/after"),
        ("8", "Benchmark/regression system — keep a baseline; revert regressions"),
        ("9", "Automated release — reproducible artifacts, signed when device-targeted"),
        ("10", "Long-term maintenance — monthly cleanup + upstream follow"),
    ],
    "other": [
        ("0", "Audit — language, entry points, packaging, upstream relationship"),
        ("1", "Unmodified build — reproduce install/build from the documented command"),
        ("2", "Baseline measurements — runtime/startup/resource usage (device steps only if on-device)"),
        ("3", "CI reliability — test/lint/package in GitHub Actions"),
        ("4", "Upstream auto-sync — track upstream; thin patch layer"),
        ("5", "Capability detection — only if the project targets devices"),
        ("6", "Profiling — CPU/memory profiling of the workload"),
        ("7", "First measured optimization — one change, benchmarked before/after"),
        ("8", "Benchmark/regression system — keep a baseline; revert regressions"),
        ("9", "Automated release — reproducible artifacts + checksums"),
        ("10", "Long-term maintenance — monthly cleanup + upstream follow"),
    ],
}


def roadmap_draft(slug, d):
    rows = PHASES.get(d.engine, PHASES["other"])
    body = "\n".join(f"| {num} | {txt} |" for num, txt in rows)
    return f"""# Roadmap — {slug} (DRAFT)

> Generated by project-intake. Phases 0..10 follow playbook
> `docs/00-quickstart.md`; the phase text is tailored to a **{d.engine}**
> project ({d.engine_note}). Review before committing.

| Phase | Goal |
|---|---|
{body}

## Current state

- `status: planning` — nothing shipped, nothing optimized yet.
- Start at phase 0 (audit) and prove phase 1 (unmodified build) before any
  optimization (golden rule: baseline first).
"""

WORKFLOW = {
    "geckoview": """## Build
./gradlew app:assembleForkRelease -PversionName=<version>   # or the project's variant
## Test / lint
./gradlew testDebugUnitTest lint
## Install to device
./gradlew installForkRelease    # or: adb install -r <apk>   (Shizuku: pm install -r)
## Benchmark (see playbook docs/07-on-device-benchmarking.md)
- cold start: `am start -W <pkg>/.HomeActivity` (before/after)
- memory: `dumpsys meminfo <pkg>`
- smoothness: `dumpsys gfxinfo <pkg> framestats`
- battery: `dumpsys batterystats` (same brightness, idle UI)
""",
    "webview": """## Build
./gradlew assembleDebug
## Test / lint
./gradlew test lint
## Install to device
./gradlew installDebug    # or: adb install -r app-debug.apk   (Shizuku: pm install -r)
## Benchmark (see playbook docs/07-on-device-benchmarking.md)
- first paint: `am start -W` + WebView `onPageFinished` timestamps
- scroll jank: `dumpsys gfxinfo <pkg> framestats`
- memory: `dumpsys meminfo <pkg>` (watch the renderer process)
""",
    "native": """## Build
cargo build --release          # Rust
# cmake --build build          # C/C++
# ./gradlew assembleRelease    # Android-native
## Test / lint
cargo test && cargo clippy -- -D warnings
# ctest            | ./gradlew test lint
## Install to device (when device-targeted)
ship the artifact; on Android: `pm install -r <apk>` via Shizuku
## Benchmark
hyperfine ./target/release/<bin>     # or criterion benches
/usr/bin/time -v ./target/release/<bin>   # peak RSS / CPU
""",
    "other": """## Build / install
<package manager> install    # e.g. npm ci | pip install -r requirements.txt
## Test / lint
npm test && npm run lint     # or: pytest && ruff check
## Benchmark
hyperfine '<run-command>'    # or node --cpu-prof / python -m cProfile
## On-device (only if this project targets a device)
see playbook docs/07-on-device-benchmarking.md; otherwise no device steps.
""",
}


def workflow_draft(slug, d):
    return f"""# Workflow — {slug} (DRAFT)

> Generated by project-intake for a **{d.engine}** project. Exact commands
> must be verified against the repo's own docs/CI before relying on them.

{WORKFLOW.get(d.engine, WORKFLOW["other"])}

## Field notes

Every problem/solution goes in the build repo's `docs/field-notes/`
(session digest -> `log.yml`), same as iceraven-op7 — the playbook sync
picks it up automatically.
"""


def prompt_draft(slug, d, repo_src):
    return f"""# Onboarding — {slug} (DRAFT)

> Generated by project-intake. Brief for whichever agent picks up this
> project next. Read the playbook `AGENTS.md` + `docs/00-quickstart.md`
> before starting.

## What this project is

- Candidate repo: `{repo_src}`
- Detected stack: **{d.engine}** ({d.engine_note})
- Status: `planning` — nothing optimized yet; baseline first.

## First steps (phases 0->2, enforced order)

1. **Audit** (phase 0) — build system, workflows, upstream relationship.
2. **Prove the unmodified build** (phase 1) — stock checkout, exact command,
   record the baseline (upstream commit, versions, artifact SHA-256).
3. **Measure on the real device** (phase 2) — label data "contended" when the
   device was in use; never present it as a clean baseline.
4. Only then optimize — one measured change per revision, benchmarked
   before/after, revert on regression.

## Rules that apply

- Baseline before optimization; never optimize on assumptions.
- Thin patch layer; never fork the app source.
- Never publish an unvalidated build; upstream conflicts stop the pipeline.
- Record every problem/solution in the build repo's `docs/field-notes/`.

## Draft provenance

Created by the project-intake skill. Review and adjust before committing
(the playbook rule: humans review and commit, agents never auto-merge).
"""


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def acquire_repo(repo_src):
    if os.path.isdir(repo_src):
        return repo_src, None
    tmp = tempfile.mkdtemp(prefix="intake-repo-")
    try:
        subprocess.run(
            ["git", "clone", "--quiet", "--depth", "1", repo_src, tmp],
            check=True, capture_output=True, text=True, timeout=600,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f"intake: cannot clone {repo_src}: {exc}")
    return tmp, tmp


def write_draft(out_root, slug, d, repo_src, dry_run):
    target = os.path.join(out_root, "projects", slug)
    if os.path.exists(target):
        dest = os.path.join(out_root, "intake-drafts", slug)
        mode = "existing -> draft dir"
    else:
        dest = target
        mode = "new -> projects/<slug>"
    files = {
        "manifest.yml": manifest_draft(slug, d),
        "roadmap.md": roadmap_draft(slug, d),
        "workflow.md": workflow_draft(slug, d),
        "PROMPT.md": prompt_draft(slug, d, repo_src),
    }
    print(f"intake: writing draft ({mode}) to {dest}")
    for name, content in files.items():
        if dry_run:
            print(f"  [dry-run] would write {name} ({len(content)} bytes)")
            continue
        os.makedirs(dest, exist_ok=True)
        path = os.path.join(dest, name)
        with open(path, "w") as fh:
            fh.write(content)
        print(f"  wrote {os.path.relpath(path, out_root)}")
    if os.path.exists(target) and not dry_run:
        print("--- diff vs existing projects/<slug> ---")
        subprocess.run(["diff", "-rq", target, dest], check=False)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="git URL or local checkout")
    ap.add_argument("--slug", required=True, help="project folder name [a-z0-9-]+")
    ap.add_argument("--out", default=os.getcwd(), help="playbook root (default: cwd)")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = ap.parse_args(argv)

    if not SLUG_RE.match(args.slug):
        sys.exit(f"intake: slug '{args.slug}' must match {SLUG_RE.pattern}")
    if not os.path.isdir(os.path.join(args.out, "projects")):
        print(f"intake: warning: {args.out} does not look like a playbook root "
              f"(no projects/ directory) — drafts will still be written under it",
              file=sys.stderr)

    repo_dir, tmp = acquire_repo(args.repo)
    try:
        d = detect(repo_dir)
        print(report(d, args.repo, args.slug))
        if d.engine is None:
            print(
                "intake: UNCLASSIFIED — refusing to force a guess.\n"
                "Proposal: extend the engine enum in scripts/validate_manifests.py "
                "with a value that fits this stack (e.g. 'electron', 'flutter', or "
                "a dedicated tool value), then re-run. Flag this repo for human "
                "review; no drafts were written.",
                file=sys.stderr,
            )
            return 3
        if args.dry_run:
            print("intake: --dry-run, nothing written")
            return 0
        write_draft(args.out, args.slug, d, args.repo, dry_run=False)
        return 0
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
