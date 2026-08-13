# 02 — Reaching the device without USB (adb off)

## Transport options, ranked

1. **adb (USB/TCP)** — full output piping, `am start -W`, `dumpsys`, Perfetto. Best for benchmarking.
2. **Shizuku** (`shizuku <cmd>` as shell) — good for install/fs/manage commands WITHOUT USB. `shizuku whoami` must print `shell`.
3. **bsh** (BeanShell in the app context) — runs Java in the app; stdout comes back as JSON `{"result":..,"output":..}`. Good for Intent/device-info queries; file access limited to app-owned storage.

## Shizuku quirks (measured, not guessed)

- `shizuku whoami` returns `shell` only when the server is running. App open ≠ server running.
- Battery optimization intermittently kills the connection. Retry loops (3–5 attempts) recover it.
- **stdout race**: the `shizuku` wrapper alternates between piping remote stdout and streaming it to the tty. Small outputs usually pipe; large outputs often go to the terminal instead, leaving local files empty.
- Fix that worked: have the remote command write to a temp file, then pull the file in a retry-until-size-match loop (`wc -c` probe, then `cat` until local size == remote size). See `automation/op7/baseline_capture.sh` in iceraven-op7.
- `shizuku cat file` streams to tty (pipe gets 0 bytes). `shizuku sh -c "cat file"` is racy. Always stage + size-check.
- Remote exit codes are unreliable through the wrapper — verify by output content, not exit code (e.g., check `pidof` output is empty, not its return code).

## Installing an APK via Shizuku

- Direct `pm install -r /sdcard/Download/x.apk` can return opaque **255**. Staging first works:
  `shizuku sh -c "cp /sdcard/Download/x.apk /data/local/tmp/x.apk && pm install -r /data/local/tmp/x.apk"`
- Verify after install: `dumpsys package <pkg>` → `versionCode`, `versionName`, `primaryCpuAbi`, and absence of `testOnly=true`.

## Files between host and device, fast

- `adb push` is the normal way; without adb, run a `python3 -m http.server` on the host (proot) bound to 127.0.0.1, then have the app fetch via `http://127.0.0.1:PORT/...` — 130 MB transferred in ~1.5 s, SHA-256 verified. No GitHub round-trip needed.
- GitHub artifact downloads truncated repeatedly on an unreliable network (4+ aborts) — prefer loopback/local transfer.
- `/sdcard` is shared between the proot and the device in this setup, but shell-created files there are NOT readable by the app user, and `chmod` fails on the FUSE filesystem. App-created files are readable. Use app storage as the transfer staging area.

## proot/bridge environment notes

- Commands run inside a proot of an assistant app on the device: `input keyevent KEYCODE_HOME` does not move focus reliably there; `am finish` does not exist on this Android version; BACK is intercepted. Warm-start measurement needs adb or a HOME-capable session.
- `host-bridge` (the local shizuku backend) is file-based IPC: write `.req`, poll for `.resp`. Races are inherent — design retries into every capture.
