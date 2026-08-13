# 01 — OnePlus 7 verified device facts

Captured on-device (BeanShell/Java bridge + sysfs), not assumed.

| Property | Value |
|---|---|
| Model | OnePlus 7 **GM1901**, board `msmnile` / `qcom` (SM8150) |
| SoC | Snapdragon 855: 1× Kryo 485 Gold 2.84 GHz, 3× 2.42 GHz, 4× Silver 1.78 GHz, 8 cores |
| GPU | Adreno 640 — OpenGL ES 3.2, Vulkan supported |
| Android | 10 (SDK 29), OxygenOS 10, build QKQ1.190716.003, kernel 4.14.117-perf |
| ABIs | arm64-v8a (primary), armeabi-v7a, armeabi — **ship arm64-v8a only** |
| RAM | 7,478 MB; heap class 256 MB / large 512 MB |
| Display | 1080×2260 @ 420 dpi |
| Storage | 256 GB UFS (239.5 GB /data, ~139 GB free at capture) |
| Media | H.264, HEVC, VP8, VP9 HW decode (Qualcomm + Codec2); **no AV1**; AC-3/AC-4/E-AC-3/FLAC audio; DivX/H.263/MPEG-4/VC-1 = software |

## Implications for special builds

- Explicit `splits.abi` = arm64-v8a → smaller APK, no useless ARM/x86 code.
- Vulkan + GLES 3.2 both present → backend choice must be benchmarked, not assumed.
- 8 GB RAM → evaluate content-process/tab-suspension policy later, after measurement.
- MediaPipe: prefer HW codec paths for H.264/HEVC/VP9; keep software fallback, especially for AV1.
