# 03 — "App not installed": root causes we hit

## The big one: android:testOnly=true

- Symptom: APK downloads, install starts, after some seconds Android says "App not installed", no error detail.
- Root cause: the CI injected `-Pandroid.injected.build.abi=...` (Studio-style flag) which made AGP emit an APK flagged `android:testOnly="true"`. Android 10 blocks UI installs of testOnly APKs (`pm install -t` only).
- Fix: patch `splits.abi` to `["arm64-v8a"]` and remove the injected flag from the workflow; add a CI gate that runs `aapt dump badging` and fails if `testOnly=true`.
- Verify: `aapt dump badging app.apk | grep -E "testOnly|native-code"` and `pm install -r` WITHOUT `-t` must succeed.

## Other causes worth checking

| Cause | Check |
|---|---|
| Wrong ABI (x86/x86_64 APK on arm64 device) | `aapt dump badging` → `native-code` |
| testOnly flag | badging → `application-debuggable`/`testOnly` |
| Signed with a different key than the installed version | `apksigner verify --print-certs` vs installed cert |
| targetSdk > device or minSdk > device | badging `sdkVersion`/`targetSdkVersion` |
| Corrupt/truncated download (SHA mismatch) | compare SHA-256 to CI-computed checksum |
| Storage (rare) | `pm install` exit code / `dumpsys package` |

## Checklist before first install attempt

1. `aapt dump badging` — package id matches, ABI matches, no testOnly.
2. APK SHA-256 matches the CI metadata.
3. `pm install -r` via adb or Shizuku; test WITHOUT `-t`.
4. Only afterwards try UI install.
