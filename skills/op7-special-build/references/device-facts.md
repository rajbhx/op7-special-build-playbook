# OnePlus 7 — verified facts (Phase 5 fingerprint)

- GM1901 (guacamoleb); Snapdragon 855 (SM8150); Adreno 640; ARM64 → `arm64-v8a` only; Android 10 OxygenOS.
- Verify on-device, never assume: ABI (`Build.SUPPORTED_ABIS`), RAM (`ActivityManager`), GLES version (`deviceConfigurationInfo.reqGlEsVersion`), Vulkan (`hasSystemFeature(FEATURE_VULKAN_HARDWARE_VERSION)`), hardware decoders (`MediaCodecList` + `isHardwareAccelerated`), display (`WindowManager`), storage (`StatFs`).
- Phase 5 logs the full fingerprint: `Log.d("OP7Capabilities", ...)` in `HomeActivity.onCreate` — read from logcat after r3 install.
- r2 baseline (contended, labeled honestly): cold start ~603 ms median; TOTAL PSS ~152 MB (1 tab); gfxinfo 8 frames / 37.5% janky; battery 15.6 mAh (partial capture). Data: `docs/performance/data/20260813-baseline-r2b/`.
- Codec policy: do not assume codec support from the chipset; read the on-device list; keep software fallback safe.
