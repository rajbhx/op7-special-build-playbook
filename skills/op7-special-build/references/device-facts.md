# OnePlus 7 — verified facts (Phase 5 fingerprint, r4 2026-08-13)

Captured on-device from `logcat -s OP7Capabilities` (r4 installed):

```
model=OnePlus:GM1901 api=29 abi=arm64-v8a+armeabi-v7a+armeabi ram=7.3G
memClass=256/512 lowRam=false gles=0x00030002 (ES 3.2) vulkan=true
hwDecoders=[avc, hevc, mp4v-es, vp8, vp9, mpeg2, wmv, divx]
display=1080x2260@420 storage=223G
```

- Android 10 (API 29), Snapdragon 855, Adreno 640, GLES 3.2 + Vulkan → full WebRender pipeline available.
- Hardware decoders confirmed: H.264, HEVC, VP8/VP9, MPEG-2, WMV, DivX. Phase 6/7 must verify GeckoView actually uses them.
- APK ships arm64-v8a only (device also supports armeabi-v7a — irrelevant, CI badging gate enforces the split).
- Package id: `io.github.forkmaintainers.iceraven.op7`; launcher activity is Fenix delegate `.App` (not HomeActivity) — resolve with `cmd package resolve-activity --brief -c android.intent.category.LAUNCHER <pkg>`.
- Install path: pull APK to `/sdcard/Download/op7/` (real storage), copy to `/data/local/tmp`, `pm install -r` (FUSE-path installs fail).
- r2 baseline (contended, labeled honestly): cold start ~603 ms median; TOTAL PSS ~152 MB (1 tab); gfxinfo 8 frames / 37.5% janky; battery 15.6 mAh partial. Data: `docs/performance/data/20260813-baseline-r2b/`.
- Codec policy: never assume codec support from the chipset; read the on-device list; keep software fallback safe.
