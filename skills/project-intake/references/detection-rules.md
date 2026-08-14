# Detection rules — signal → engine mapping

Canonical rules used by `scripts/intake.py`. The manifest `engine` enum is
fixed (`geckoview | webview | native | other`); extending it requires a change
to `scripts/validate_manifests.py` and is flagged for human review — intake
never drafts on a guess.

## Signals scanned (top of the tree, ignored dirs skipped)

| Signal | Where it appears | Means |
|---|---|---|
| `AndroidManifest.xml` | root or `app/src/main/` | Android app |
| `build.gradle[.kts]`, `settings.gradle[.kts]`, `gradlew` | root / `app/` | Gradle build |
| `org.mozilla.geckoview`, `geckoview-omni`, `org.mozilla:geckoview`, `org.mozilla.components`, `mozilla-central`, `android-components` | any gradle file | **GeckoView stack** |
| `android.webkit.WebView` / `WebViewClient` / `WebChromeClient` | `.java`/`.kt` (head of file) | **WebView stack** (only counts when GeckoView markers are absent) |
| `capacitor` | `package.json` / gradle | system-WebView wrapper → `webview` |
| `tauri` | `Cargo.toml` | system-WebView wrapper → `webview` |
| `electron` | `package.json` | Chromium wrapper → `webview` |
| `pubspec.yaml` + `flutter:` | root | Flutter → `native` (Flutter engine) |
| `Cargo.toml` | root / crates | Rust → `native` (unless tauri) |
| `CMakeLists.txt`, `*.sln`/`*.csproj`, `*.xcodeproj`, `Package.swift` | root | compiled native |
| `package.json` (no electron) | root | Node/JS → `other` |
| `pyproject.toml` / `requirements.txt` / `setup.py` | root | Python → `other` |

## Priority (first clean match wins)

1. GeckoView markers → `geckoview`
2. WebView usage (no GeckoView) → `webview`
3. Capacitor/Tauri/Electron → `webview` (system webview wrappers)
4. Flutter → `native`
5. Rust (no Tauri) / CMake / .NET / Swift → `native`
6. Node (no Electron) / Python → `other`
7. No signal → **unclassified**: print the evidence, propose an enum
   extension, exit without drafting.

## Confidence + notes

- High: a primary marker file was found and read (e.g. geckoview dep line).
- Medium: inferred from a secondary marker (e.g. `gradlew` exists but no
  manifest — Android-ish, needs confirmation).
- Every classification prints the exact evidence lines so the review can
  verify the mapping, not just trust the label.

## ABI discovery (best effort, never guessed)

- Gradle `abiFilters` / `splits { abi }` / `ndk { abiFilters }` → the listed
  ABIs.
- `.so` paths under `app/src/main/jniLibs/` or `libs/` → ABIs seen in the
  folder names (`arm64-v8a`, `armeabi-v7a`, `x86_64`, ...).
- Rust `Cargo.toml` `[target.*]` or `.cargo/config.toml` targets.
- Nothing found → `abi: TODO` in the draft (never invented).

## Edge cases

- **Electron** looks like Node but wraps Chromium: maps to `webview` with a
  note; if you want a dedicated `electron` engine value, extend the enum —
  intake will flag it.
- **Flutter** is compiled (Skia/Impeller), not a webview: `native`.
- **Capacitor** embeds the system WebView: `webview`.
- **Monorepos**: scan the root plus one level of `apps/`, `packages/`,
  `src/`; if two engines appear, prefer the one with more evidence and note
  the other in the detection report.
- **Empty / docs-only repos**: no signals → flagged, not forced to `other`.
